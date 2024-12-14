import os
from gaming import models

from django.shortcuts import render
from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView, Response, Request, status

from google.oauth2 import id_token
from google.auth.transport import requests

from .models import AnswerRecord, BattleRecord, User
from .serializers import UserSignupSerializer, UserSigninSerializer, UserSerializer

class AuthGoogle(APIView):
    """
    API to handle google log in
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            user_data = self.get_google_user_data(request)
            print(f"get user data, {user_data}")
        except ValueError as e:
            print(e)
            return HttpResponse("Invalid Google token", status=403)

        email = user_data["email"]
        
        # update model
        user, created = User.objects.get_or_create(
            google_username=email,
            defaults={
                "email": email, 
                "name": user_data.get("name"),
            }
        )

        refresh = RefreshToken.for_user(user)

        user_ser = UserSerializer(user)
        serialized_user = user_ser.data
    
        return Response({
            "access_token": str(refresh.access_token),
            **serialized_user,
        }, status=status.HTTP_200_OK)

    @staticmethod
    def get_google_user_data(request: Request):
        print("getting google user data")
        body = request.data
        token = body.get("id_token")

        if not token:
            raise ValueError("no id_token provided")


        user_data = None
        try:
            user_data = id_token.verify_oauth2_token(
                token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
            )
        except:
            user_data = id_token.verify_oauth2_token(
                token, requests.Request(), os.environ['GOOGLE_OAUTH_IOS_ID']
            )
        
        return user_data
    

class TokenLogin(APIView):
    """
    Sign in with token to get user data
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        user = request.user
        user_ser = UserSerializer(user)
        serialized_user = user_ser.data

        return Response({
            **serialized_user,
        }, status=status.HTTP_200_OK)


class UserSignUp(APIView):
    """
    Handles user signup by validating and creating new user accounts, 
    generating tokens, and setting cookies for authentication.
    """
    def post(self, request):
        required_fields = ['email', 'username', 'password', 'name']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {"error": f"The '{field}' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if the user already exists
        if User.objects.filter(username=request.data['username']).exists():
            return Response(
                {"error": "A user with this email or username already exists."},
                status=status.HTTP_409_CONFLICT
            )

        # Proceed with user creation if validations pass
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate both access and refresh tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # user data
            user_ser = UserSerializer(user)
            serialized_user = user_ser.data
            print(f"user data is {serialized_user}")

            return Response({
                "access_token": access_token,
                **serialized_user,
            }, status=status.HTTP_200_OK)
        
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogin(APIView):
    """
    Handles user login by validating credentials, generating tokens,
    and setting cookies for authentication.
    """
    def post(self, request):
        required_fields = ['username', 'password']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {"error": f"The '{field}' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )


        username = request.data.get('username')
        password = request.data.get('password')
    
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Generate tokens
            refresh = RefreshToken.for_user(user)

            # user data
            user_ser = UserSerializer(user)
            serialized_user = user_ser.data
            print(f"user data is {serialized_user}")

            return Response({
                "access_token": str(refresh.access_token),
                **serialized_user,
            }, status=status.HTTP_200_OK)
        
        else:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

class CheckUsername(APIView):
    """
    Check if the username is already taken
    """
    def post(self, request):
        required_fields = ['username']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {"error": f"The '{field}' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )


        username = request.data.get('username')

        if User.objects.filter(username=username).exists():
            return Response({"message": "username already taken"}, status=status.HTTP_409_CONFLICT)
        else:
            return Response({"message": "username is available"}, status=status.HTTP_200_OK)
        
class CheckEmail(APIView):
    """
    Check if the email is valid or not
    """
    def post(self, request):

        required_fields = ['email']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {"error": f"The '{field}' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        email = request.data.get('email')

        try:
            validate_email(email)
        except:
            return Response({"message": "email is invalid"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"message": "email already taken"}, status=status.HTTP_409_CONFLICT)
        
        return Response({"message": "email is available"}, status=status.HTTP_200_OK)

# @method_decorator(csrf_exempt, name='dispatch')
class SignOut(APIView):
    """
    Delete signed in token
    """
    def post(self, request, *args, **kwargs):
        return Response({"message": "deleted"}, status=status.HTTP_204_NO_CONTENT)
    
class UserAPI(APIView):
    """
    PATCH: update user information
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request: Request):
        permitted_fields = ["name"]
        body = request.data

        for k in body.keys():
            if k not in permitted_fields:
                return Response(
                    {"error": f"the field {k} is not permitted"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        user: User = request.user
        
        for attr, value in body.items():
            setattr(user, attr, value)
        
        user.save()

        return Response({
            "message": "user updated"
        }, status=status.HTTP_200_OK)

# Create your views here.
class Record(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the user record, maybe analyse the improve rate in the future
        
        Response Data:
        {
            "sanrio": {
                "field": "sanrio",
                "totCorrect": 60,
                "totWrong": 40,
                "correctRate": 0.6,
                # "improveRate": 10%,
            },
            "highschool": {
                "field", "highschool",
                "totCorrect": 60,
                "totWrong": 40,
                "correctRate": 0.6,
                # "improveRate": 10%,
            },
        }
        """

        try:
            user = request.user
            fieldRecordRes = {}

            for field in models.field_choice:
                fieldKey = field[1]
                print(f"finding record for {fieldKey}")

                records = AnswerRecord.objects.filter(
                    user=user,
                    field=fieldKey,
                )

                totCorrect = 0
                totWrong = 0

                for rec in records:
                    totCorrect += rec.totCorrect
                    totWrong += rec.totWrong
                
                correctRate = 0.0 if (totCorrect + totWrong) == 0 else totCorrect / (totCorrect + totWrong)

                fieldRecordRes[fieldKey] = {
                    "field": fieldKey,
                    "totCorrect": totCorrect,
                    "totWrong": totWrong,
                    "correctRate": correctRate,
                }
            
            return Response(fieldRecordRes, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"error": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """ 
        Update the user record

        request.data:
        {
            "field": "nursing",
            "totCorrect": 10,
            "totWrong": 2,
            "opponent": "user2",
            "victory": True,
        }
        """
        try:
            # update the answer record
            AnswerRecord.objects.create(
                user=request.user,
                field=request.data["field"],
                totCorrect=request.data["totCorrect"],
                totWrong=request.data["totWrong"],
            )

            # update the battle record
            if request.data["victory"]:
                opponent = list(User.objects.filter(username=request.data["opponent"]))[0]
                BattleRecord.objects.create(winner=request.user, loser=opponent, field=request.data["field"])
            
            return Response({"message": "updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            raise e