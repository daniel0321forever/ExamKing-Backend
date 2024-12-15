import os
import json

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

from .models import AnswerRecord, BattleRecord, User, Problem
from .serializers import UserSignupSerializer, UserSigninSerializer, UserSerializer
from .algo import hash_problem

class AuthGoogle(APIView):
    """
    API to handle Google login.

    POST /auth/
    -----------
    Request Body:
    {
        "id_token": "string"
    }

    Response:
    - Success (200 OK):
    {
        "access_token": "string",
        "id": "integer",
        "email": "string",
        "name": "string",
        "username": "string"
    }
    - Failure (403 Forbidden):
    {
        "error": "Invalid Google token"
    }
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
    Sign in with token to get user data.

    POST /token_login/
    ------------------
    Request Headers: Authorization header with Bearer token.

    Response:
    - Success (200 OK):
    {
        "id": "integer",
        "email": "string",
        "name": "string",
        "username": "string"
    }
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

    POST /signup/
    -------------
    Request Body:
    {
        "email": "string",
        "username": "string",
        "password": "string",
        "name": "string"
    }

    Response:
    - Success (200 OK):
    {
        "access_token": "string",
        "id": "integer",
        "email": "string",
        "name": "string",
        "username": "string"
    }
    - Failure (400 Bad Request):
    {
        "error": "The 'field' field is required."
    }
    - Failure (409 Conflict):
    {
        "error": "A user with this email or username already exists."
    }
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

    POST /login/
    ------------
    Request Body:
    {
        "username": "string",
        "password": "string"
    }

    Response:
    - Success (200 OK):
    {
        "access_token": "string",
        "id": "integer",
        "email": "string",
        "name": "string",
        "username": "string"
    }
    - Failure (401 Unauthorized):
    {
        "error": "Invalid credentials."
    }
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
    Check if the username is already taken.

    POST /check_username/
    ---------------------
    Request Body:
    {
        "username": "string"
    }

    Response:
    - Success (200 OK):
    {
        "message": "username is available"
    }
    - Failure (409 Conflict):
    {
        "message": "username already taken"
    }
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
    Check if the email is valid or not.

    POST /check_email/
    ------------------
    Request Body:
    {
        "email": "string"
    }

    Response:
    - Success (200 OK):
    {
        "message": "email is available"
    }
    - Failure (400 Bad Request):
    {
        "message": "email is invalid"
    }
    - Failure (409 Conflict):
    {
        "message": "email already taken"
    }
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
    Delete signed in token.

    POST /signout/
    --------------
    Response:
    - Success (204 No Content):
    {
        "message": "deleted"
    }
    """
    def post(self, request, *args, **kwargs):
        return Response({"message": "deleted"}, status=status.HTTP_204_NO_CONTENT)
    
class UserAPI(APIView):
    """
    PATCH: update user information.

    PATCH /user/
    ------------
    Request Headers: Authorization header with Bearer token.
    Request Body:
    {
        "name": "string"
    }

    Response:
    - Success (200 OK):
    {
        "message": "user updated"
    }
    - Failure (400 Bad Request):
    {
        "error": "the field 'field_name' is not permitted"
    }
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
    """
    Manage user records.

    GET /record/
    ------------
    Request Headers: Authorization header with Bearer token.

    Response:
    - Success (200 OK):
    {
        "field_name": {
            "field": "string",
            "totCorrect": "integer",
            "totWrong": "integer",
            "correctRate": "float"
        },
        ...
    }

    POST /record/
    -------------
    Request Headers: Authorization header with Bearer token.
    Request Body:
    {
        "field": "string",
        "totCorrect": "integer",
        "totWrong": "integer",
        "opponent": "string",
        "victory": "boolean"
    }

    Response:
    - Success (200 OK):
    {
        "message": "updated"
    }
    """
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

class InitializeProblem(APIView):
    """
    Initialize problems from a JSON file.

    POST /initialize_problem/
    -------------------------
    Request Headers: Authorization header with Bearer token.

    Response:
    - Success (200 OK):
    {
        "message": "initialized"
    }
    - Failure (403 Forbidden):
    {
        "error": "no permission"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            if user.username != os.environ["ADMIN_USERNAME"]:
                return Response({"error": "no permission"}, status=status.HTTP_403_FORBIDDEN)
            
            with open('gaming/problems.json', 'r') as f:
                all_problems = json.load(f)

                for key, item in all_problems.items():
                    for problem in item:
                        hashed_id = hash_problem(problem)
                        
                        problem, created = Problem.objects.get_or_create(
                            hashed_id=hashed_id,
                            defaults={
                                "field": key,
                                "problem": problem["problem"],
                                "options": problem["options"],
                                "answer": problem["answer"],
                                "correct_rate": problem.get("correct_rate", 60.0),
                            }
                        )

                        if created:
                            print(f"problem {problem['problem']} is initialized")

                return Response({"message": "initialized"}, status=status.HTTP_200_OK)
    
        except Exception as e:
            raise e

        