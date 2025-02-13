# backend/api/views.py
from rest_framework import viewsets, status, permissions
from .models import User, Track, License
from .serializers import UserSerializer, TrackSerializer, LicenseSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings  # We still import settings, but don't use it for B2
from django.utils import timezone
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from supabase import create_client, Client
import os

# Initialize Supabase client outside the class, using environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to register

    def create(self, request, *args, **kwargs):
        # 1. Sign up the user with Supabase FIRST
        email = request.data.get('email')
        password = request.data.get('password')
        username = request.data.get('username')

        if not all([email, password, username]):  # Basic validation
            return Response({"error": "Email, password, and username are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Sign up with Supabase
            res = supabase.auth.sign_up({"email": email, "password": password})

            # Check for errors from Supabase
            if res.user is None:
                # Assuming 'res' has an 'error' attribute, and it is not None
                if hasattr(res, 'error') and res.error is not None:
                    return Response({"error": str(res.error)}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Handle cases where there might be no 'error' attribute, but signup failed.
                    return Response({"error": "Supabase signup failed for unknown reason."}, status=status.HTTP_400_BAD_REQUEST)

            supabase_user_id = res.user.id # Get user id

        except Exception as e:  # Catch any exceptions during Supabase signup
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 2.  NOW create the Django user, using the Supabase ID
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save(id=supabase_user_id)

        # 3. Get JWT token
        refresh = RefreshToken.for_user(user)
        token_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response({
            "user": UserSerializer(user).data,
            "token": token_data
        }, status=status.HTTP_201_CREATED)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    # permission_classes and authentication_classes will be inherited from settings.py

    def perform_create(self, serializer):
        # Handle file upload to B2
        file = self.request.FILES.get('track')
        if not file:
            return Response({"detail": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique filename
        file_extension = file.name.split('.')[-1]
        user_id = self.request.user.id  # Get user ID from the authenticated request
        unique_filename = f"{user_id}-{file.name}-{timezone.now().strftime('%Y%m%d%H%M%S')}.{file_extension}"

        # Upload to B2 using region_name (RECOMMENDED)
        s3 = boto3.client('s3',
                          region_name="us-west-004",  # Use region_name
                          aws_access_key_id=os.environ.get('B2_KEY_ID'),
                          aws_secret_access_key=os.environ.get('B2_APPLICATION_KEY')
                          )
        try:
            s3.upload_fileobj(file, os.environ.get('B2_BUCKET_NAME'), unique_filename)
            # Construct the URL *after* successful upload:
            file_url = f"https://{os.environ.get('B2_BUCKET_NAME')}.s3.us-west-004.backblazeb2.com/{unique_filename}"
        except NoCredentialsError:
            return Response({"detail": "Credentials not available."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ClientError as e:  # Catch Boto3-specific client errors
            return Response({"detail": f"B2 upload error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer.save(user=self.request.user, file_path=file_url, preview_path=file_url)

    def get_queryset(self):
        # Filter tracks by user if `user_id` query parameter is provided
        user_id = self.request.query_params.get('user_id')
        queryset = self.queryset
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        return queryset

    # Add the list method, for /api/tracks
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LicenseViewSet(viewsets.ModelViewSet):
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    # permission_classes will be inherited