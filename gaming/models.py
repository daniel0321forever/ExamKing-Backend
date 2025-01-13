from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from uuid import uuid4

NURSING = "Nursing"
SANRIO = "Sanrio"
HIGHSCHOOL = "highschool"
BIOLOGY = "biology"

field_choice = (
    (NURSING, "nursing"),
    (SANRIO, "sanrio"),
    # (HIGHSCHOOL, "highschool"),
    (BIOLOGY, "biology"),
)

LEARNING = "learning"
REVIEWING = "reviewing"
MASTERED = "mastered"

word_learning_status = (
    (LEARNING, "learning"),
    (REVIEWING, "reviewing"),
    (MASTERED, "mastered"),
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Meta:
        db_table = "custom_user"

    id = models.UUIDField(primary_key=True, default=uuid4,
                          editable=False, unique=True)
    name = models.CharField(max_length=64)
    email = models.EmailField(blank=True, default='')
    username = models.CharField(
        max_length=255, blank=True, unique=True, null=True)
    google_username = models.CharField(
        max_length=255, blank=True, unique=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    hesitations = models.ManyToManyField(
        'Word', through='Hesitation', blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email

# TODO: change answer record to make it correpspond to one problem for each record


class AnswerRecord(models.Model):
    class Meta:
        db_table = "answer_record"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    field = models.CharField(max_length=32, choices=field_choice)
    totCorrect = models.IntegerField()
    totWrong = models.IntegerField()
    createdTime = models.DateTimeField(auto_now_add=True)


class UniqueAnswerRecord(models.Model):
    class Meta:
        db_table = "unique_answer_record"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(
        'Problem', on_delete=models.CASCADE)
    correct = models.BooleanField()
    createdTime = models.DateTimeField(auto_now_add=True)


class BattleRecord(models.Model):
    class Meta:
        db_table = "battle_record"

    winner = models.ForeignKey(
        User, related_name="win_record", on_delete=models.SET_NULL, null=True)
    loser = models.ForeignKey(
        User, related_name="lose_record", on_delete=models.SET_NULL, null=True)
    field = models.CharField(max_length=32, choices=field_choice)


class Problem(models.Model):
    class Meta:
        db_table = "problem"

    hashed_id = models.CharField(max_length=256, primary_key=True, unique=True)
    word = models.ForeignKey('Word', on_delete=models.SET_NULL, null=True)
    field = models.CharField(max_length=32, choices=field_choice)
    problem = models.CharField(max_length=512)
    answer = models.IntegerField()
    options = models.JSONField()
    correct_rate = models.FloatField(default=60.0)


class Word(models.Model):
    class Meta:
        db_table = "word"

    word = models.CharField(primary_key=True, max_length=256, unique=True)
    level = models.IntegerField()
    hesitations = models.ManyToManyField(
        'User', through='Hesitation', blank=True)

    def __str__(self):
        return self.word


class Definition(models.Model):
    class Meta:
        db_table = "definition"

    word = models.ForeignKey('Word', on_delete=models.CASCADE)
    definition = models.CharField(max_length=512)
    part_of_speech = models.CharField(max_length=256)
    example = models.CharField(max_length=1024)
    translation = models.CharField(max_length=256)

    def __str__(self):
        return self.definition


class WordLearningRecord(models.Model):
    class Meta:
        db_table = "word_learning_record"

    word = models.ForeignKey('Word', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=word_learning_status)
    created_time = models.DateField(auto_now_add=True)


class Hesitation(models.Model):
    class Meta:
        db_table = "hesitation"

    word = models.ForeignKey('Word', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    duration = models.DurationField()
    created_time = models.DateTimeField(auto_now_add=True)
