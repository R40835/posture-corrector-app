from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField


# Creating Database Tables
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(email, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


# using a custom user model to login with email
class User(AbstractBaseUser):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, unique=True)
    profile_picture = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new user
        super().save(*args, **kwargs)
        if is_new:
            Notifications.objects.create(subject=self, back_alert=0, neck_alert=0)


class Notifications(models.Model):
    subject = models.ForeignKey(User, on_delete=models.CASCADE)
    back_alert = models.IntegerField(default=0)
    neck_alert = models.IntegerField(default=0)


class Videos(models.Model):
    subject = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_created=False, null=False, blank=False)
    end_time = models.DateTimeField(auto_created=False, null=False, blank=False)
    total_time_seconds = models.IntegerField(default=0)
    total_alerts = models.IntegerField(default=0)
    incorrect_postures = ArrayField(models.CharField(max_length=20), blank=True, null=True)
    posture_score = models.IntegerField(default=0, null=False, blank=False)


class FeedBack(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    opinion = models.TextField(null=False, blank=False, max_length=500)
    date_created = models.DateTimeField(auto_now=True)


class PoorPostures(models.Model):
    subject = models.ForeignKey(User, on_delete=models.CASCADE)
    posture_photo = models.ImageField(upload_to='poor_postures/', null=False, blank=False)
    date_created = models.DateTimeField(auto_now=True)