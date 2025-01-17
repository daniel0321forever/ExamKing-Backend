from .algo import hash_problem
from .serializers import UserSignupSerializer, UserSigninSerializer, UserSerializer
from .models import *
import os
import json
from datetime import datetime, timedelta

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
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


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
        "stats": {
            "correct_rate": {
                "maxVal": 100.0,
                "val": 31.2
            },
            "win_rate": {
                "maxVal": 100.0,
                "val": 51.3
            },
            "avg_words": {
                "maxVal": 100.0,
                "val": 35.1
            }
        },
        ...
    }

    POST /record/
    -------------
    Request Headers: Authorization header with Bearer token.
    Request Body:
    {
        "field": "string",
        "victory": true,
        "records": [
            {
                "problem_id": "135jjsw",
                "correct": false,
            },
            {
                "problem_id": "3gg344h",
                "correct": false,
            }
        ]
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
        """

        user = request.user
        stats = []

        # correct rate
        correct = UniqueAnswerRecord.objects.filter(
            user=user, correct=True).count()
        total = UniqueAnswerRecord.objects.filter(
            user=user).count()
        correct_rate = correct / total if total > 0 else 0

        stats.append(
            {
                "key": "correct_rate",
                "maxVal": 100.0,
                "val": correct_rate * 100,
            }
        )

        # win rate
        win = BattleRecord.objects.filter(
            winner=user).count()
        total = BattleRecord.objects.filter(
            models.Q(winner=user) | models.Q(loser=user)).count()
        win_rate = win / total if total > 0 else 0

        stats.append(
            {
                "key": "win_rate",
                "maxVal": 100.0,
                "val": win_rate * 100,
            }
        )

        # avg words
        avg_words = 0
        first_word = WordLearningRecord.objects.filter(
            user=user).order_by('created_time').first()

        if first_word:
            first_word_date = first_word.created_time

            today = datetime.now().date()
            days = (today - first_word_date).days + 1

            avg_words = WordLearningRecord.objects.filter(
                user=user).count() / days if days > 0 else 0

        stats.append(
            {
                "key": "avg_words",
                "maxVal": 100.0,
                "val": avg_words,
            }
        )

        return Response(stats, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Update the user record
        """

        field = request.data["field"]
        records = request.data["records"]
        for record in records:
            problem = Problem.objects.get(hashed_id=record["problem_id"])
            correct = record["correct"]

            # update the answer record
            UniqueAnswerRecord.objects.create(
                user=request.user,
                problem=problem,
                correct=correct,
            )

        # update the battle record
        if request.data["victory"]:
            opponent = User.objects.filter(
                username=request.data["opponent"]).first()
            BattleRecord.objects.create(
                winner=request.user, loser=opponent, field=request.data["field"])

        return Response({"message": "updated"}, status=status.HTTP_200_OK)


class WordAPI(APIView):
    """
    Manage word records.

    GET /word/
    ------------
    Request Headers: Authorization header with Bearer token.
    Request Body:
    {
        "level": "integer"
    }   

    Response:
    - Success (200 OK):
    {
        "words": [
            {
                "word": "string",
                "definition": "string",
            }
        ]
    }   

    POST /word/
    ------------
    Request Headers: Authorization header with Bearer token.
    Request Body:
    {
        "word": "string",
        "status": "string"
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
        Get the user word record, maybe analyse the improve rate in the future
        """

        level = request.GET.get("level")
        words = Word.objects.filter(level=level)

        serialized_words = [
            {
                "word": word.word,
                "definition": Definition.objects.filter(word=word).first().definition,
                "translation": Definition.objects.filter(word=word).first().translation,
                "partOfSpeech": Definition.objects.filter(word=word).first().part_of_speech,
                "example": Definition.objects.filter(word=word).first().example,
                "level": word.level,
                "isLearned": WordLearningRecord.objects.filter(
                    user=request.user, word=word).first().status == REVIEWING if len(WordLearningRecord.objects.filter(
                        user=request.user, word=word)) > 0 else False,
                "seenCount": WordLearningRecord.objects.filter(
                    user=request.user, word=word).count(),
            } for word in words
        ]

        return Response(serialized_words, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Update the user word record
        """

        word = request.data["word"]
        word_object = None

        try:
            word_object = Word.objects.get(word=word)
        except Word.DoesNotExist:
            return Response({"error": "word not found"}, status=status.HTTP_404_NOT_FOUND)

        learning_status = request.data["status"]

        WordLearningRecord.objects.create(
            user=request.user, word=word_object, status=learning_status)

        return Response({"message": "updated"}, status=status.HTTP_200_OK)


class WordProgressAPI(APIView):
    """
    Get the user word progress

    GET /word_progress/
    ---------------------
    Request Headers: Authorization header with Bearer token.

    Response:
    - Success (200 OK):

    POST /word_progress/
    ---------------------
    Request Headers: Authorization header with Bearer token.
    Request Body:
    {
        "word": "string",
        "status": "string"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the user word progress
        """
        word_progress = []

        today = datetime.today()
        start_of_month = today.replace(day=1)

        current_date = start_of_month
        while current_date <= today:
            # Perform actions for each day here

            word_learning_record = WordLearningRecord.objects.filter(
                user=request.user, created_time=current_date.date()
            ).count()

            word_progress.append(word_learning_record)

            current_date += timedelta(days=1)

        return Response(word_progress, status=status.HTTP_200_OK)


class CorrectRateAPI(APIView):
    """
    Get the user correct rate

    GET /correct_rate/
    ---------------------
    Request Headers: Authorization header with Bearer token.

    Response:
    - Success (200 OK):
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the user correct rate
        """
        correct_rate = []

        today = datetime.today()
        start_date = today - timedelta(days=6)

        current_date = start_date
        while current_date <= today:
            # Perform actions for each day here
            current_date += timedelta(days=1)

            correct_answers = UniqueAnswerRecord.objects.filter(
                user=request.user, createdTime__date=current_date.date(), correct=True
            ).count()

            total_answers = UniqueAnswerRecord.objects.filter(
                user=request.user, createdTime__date=current_date.date()
            ).count()

            if total_answers > 0:
                daily_correct_rate = (correct_answers / total_answers) * 100
            else:
                daily_correct_rate = 0

            correct_rate.append(daily_correct_rate)

        return Response([correct_rate], status=status.HTTP_200_OK)


class CreateArticle(APIView):
    """
    Create an article from specified words

    GET /create_article/
    -----------------------
    Request Headers: Authorization header with Bearer token.
    Request Query:
    {
        "level": "integer"
    }

    Response:
    - Success (200 OK):
    {
        "article": "string"
    }
    """
    permission_classes = [IsAuthenticated]

    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

    # Create the model
    _query_generation_model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config={
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        },
    )

    chat_history = []

    @classmethod
    def _send_message(cls, model: genai.GenerativeModel, message: str) -> str:
        chat_session = model.start_chat(history=[])

        response = chat_session.send_message(message)
        return response.text

    def get(self, request):
        level = int(request.GET.get("level"))
        words = Word.objects.filter(level=level).order_by('?')[:10]

        prompt = f"""
make me a article with 300 words that must include the following words: {words}. 
The article doesn't have to be great, but must include the the words mentioned. 
The response should be in plain text format that only contain the article without any other words, and the included words in the article should be marked with @word&
"""
        print(prompt)

        response = self._send_message(self._query_generation_model, prompt)

        print(response)

        return Response({"article": response}, status=status.HTTP_200_OK)


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

        with open("gaming/words.json", "r") as f:
            word_list = json.load(f)

        for word in word_list:
            word_object, created = Word.objects.get_or_create(
                word=word["word"],
                defaults={
                    "word": word["word"],
                    "level": word["level"],
                }
            )

            for definition in word["definitions"]:
                Definition.objects.get_or_create(
                    word=word_object,
                    definition=definition["definition"],
                    part_of_speech=definition["part_of_speech"],
                    example=definition["example"],
                    translation=definition["translation"],
                )

        user = request.user
        if user.username != os.environ["ADMIN_USERNAME"]:
            return Response({"error": "no permission"}, status=status.HTTP_403_FORBIDDEN)

        Problem.objects.all().delete()  # TODO: remove this after testing

        # initialize problems
        with open('gaming/problems.json', 'r') as f:
            all_problems = json.load(f)

            for key, item in all_problems.items():
                for problem in item:
                    hashed_id = hash_problem(problem)

                    print(f"word is {problem.get('word', None)}")

                    problem_object, created = Problem.objects.get_or_create(
                        hashed_id=hashed_id,
                        defaults={
                            "field": key,
                            "problem": problem["problem"],
                            "options": problem["options"],
                            "answer": problem["answer"],
                            "correct_rate": problem.get("correct_rate", 60.0),
                            "word": Word.objects.get(word=problem.get("word", None)) if problem.get("word", None) else None,
                        }
                    )

                    if created:
                        print(
                            f"problem {problem['problem']} is initialized")

        return Response({"message": "initialized"}, status=status.HTTP_200_OK)
