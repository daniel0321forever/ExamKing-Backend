from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db.models import QuerySet

from .models import User

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'name']

    def validate(self, data):
        # Check for required fields
        if not data.get("username") or not data.get("password") or not data.get("email"):
            raise serializers.ValidationError("MISSING_FIELDS")

        # Check if username already exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("USERNAME_EXISTS")

        return data

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class UserSigninSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials") 
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
    
    def to_representation(self, user: User):
        win_record: QuerySet = user.win_record.all()
        lose_record: QuerySet = user.lose_record.all()
        win_rate = win_record.count() / (win_record.count() + lose_record.count()) if win_record.count() + lose_record.count() > 0 else 0.0

        user_repr_dict = {
            "id": user.id,
            "google_username": user.google_username,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "photo_url": "",
            "win_record": win_record.count(),
            "lose_record": lose_record.count(),
            "win_rate": win_rate
        }

        return user_repr_dict