from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Permission(models.Model):
  name = models.CharField(max_length=100, unique=True)
  codename = models.CharField(max_length=100, unique=True)

  def __str__(self):
    return self.name
  

class Role(models.Model):
  name = models.CharField(max_length=50, unique=True)
  permissions = models.ManyToManyField(Permission, blank=True)

  def __str__(self):
    return self.name
  

class CustomUser(AbstractUser):
  role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

  def has_custom_permission(self, codename):
    if self.role:  # does the user even have a Role assigned
        return self.role.permissions.filter(codename=codename).exists()  # looking at the User's role and then at their permissions, searching for the codename of a permission
    return False


class Credential(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="credentials")
  website_name = models.CharField(max_length=100)
  email = models.EmailField()
  username = models.CharField(max_length=100)
  password = models.CharField(max_length=255)
  url = models.URLField()
  logo = models.CharField(max_length=255, null=True, blank=True)

  def __str__(self):
    return f"{self.website_name} - {self.username}"
  

class Note(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notes")
  headline = models.CharField(max_length=200)
  bodytext = models.TextField()
  logo = models.CharField(max_length=255, default="manager/assets/NotesIcon.png")
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.headline



