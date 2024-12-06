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

        # Add any other logic, such as setting a http only auth cookie as needed here.
        refresh = RefreshToken.for_user(user)

        win_rate = win_record.count() / (win_record.count() + lose_record.count()) if win_record.count() + lose_record.count() > 0 else 0.0
    
        return Response({
            "access_token": str(refresh.access_token),
            "name": user.name,
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

        return id_token.verify_oauth2_token(
            token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
        )

    

# @method_decorator(csrf_exempt, name='dispatch')
class SignOut(APIView):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    def post(self, request, *args, **kwargs):

        # update model

        return Response({"message": "deleted"}, status=status.HTTP_204_NO_CONTENT)


# Create your views here.
class Record(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Get the user record """
        try:
            return Response(status=status.HTTP_200_OK)
            # token = request.META.get("HTTP_AUTHORIZATION").split(" ")[1]
            # tokenObject = models.Token.objects.get(token=token)
            # user = tokenObject.user

            # # get the battle record
            # battleRecord = user.win_record
            # print(battleRecord)

            # return Response({"messgage": "found battle record"}, status=status.HTTP_200_OK)
        
        except models.Token.DoesNotExist:
            print("cannot find token")
            return Response({"error": "invalid token"}, status=status.HTTP_403_FORBIDDEN)
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
                BattleRecord.objects.create(winner=request.user, loser=request.data["opponent"], field=request.data["field"])
            
            return Response({"message": "updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            raise e