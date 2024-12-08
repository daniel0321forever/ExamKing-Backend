import os
from gaming import models

from django.shortcuts import render
from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView, Response, Request, status

from google.oauth2 import id_token
from google.auth.transport import requests

from .models import AnswerRecord, BattleRecord, User

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
            username=email,
            defaults={
                "email": email, 
                "name": user_data.get("name"),
            }
        )

        # get battle record
        win_record: QuerySet = user.win_record.all()
        lose_record: QuerySet = user.lose_record.all()
        win_rate = win_record.count() / (win_record.count() + lose_record.count()) if win_record.count() + lose_record.count() > 0 else 0.0

        refresh = RefreshToken.for_user(user)
    
        return Response({
            "access_token": str(refresh.access_token),
            "name": user.name,
            "username": user.username,
            "photo_url": user_data.get('picture', None),
            "win_record": win_record.count(),
            "lose_record": lose_record.count(),
            "win_rate": win_rate
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
    

class TokenSignIn(APIView):
    """
    Sign in with token to get user data
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        user = request.user

        win_record: QuerySet = user.win_record.all()
        lose_record: QuerySet = user.lose_record.all()
        win_rate = win_record.count() / (win_record.count() + lose_record.count()) if win_record.count() + lose_record.count() > 0 else 0.0

        return Response({
            "name": user.name,
            "username": user.username,
            "photo_url": "",
            "win_record": win_record.count(),
            "lose_record": lose_record.count(),
            "win_rate": win_rate
        }, status=status.HTTP_200_OK)


# @method_decorator(csrf_exempt, name='dispatch')
class SignOut(APIView):
    """
    Delete signed in token
    """
    def post(self, request, *args, **kwargs):

        # update model

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