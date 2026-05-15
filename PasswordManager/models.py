from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
import uuid


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

  # MFA fields
  is_mfa_enabled = models.BooleanField(default=False)
  mfa_secret = models.CharField(max_length=32, blank=True, null=True)  # for TOTP (Google Authentication)
  
  backup_code = models.JSONField(default=list, blank=True) # to store one-time use recovery codes

  def has_custom_permission(self, codename):
    if self.role:  # does the user even have a Role assigned
        return self.role.permissions.filter(codename=codename).exists()  # looking at the User's role and then at their permissions, searching for the codename of a permission
    return False
  

class RecoveryKey(models.Model):  # this is used in case the user forgets their master key
  user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
  encrypted_master_key_backup = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)


class EmergencyAccessCode(models.Model):  # this is used as a third way of verification (in case the user losses their phone and cannot use Google Authentication)
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='emergency_codes')
  code_hash = models.CharField(max_length=128) # hashed for security
  used = models.BooleanField(default=False)


class UserSession(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
  session_key = models.CharField(max_length=40, unique=True)
  ip_address = models.GenericIPAddressField(null=True, blank=True)
  user_agent = models.TextField(null=True, blank=True) # Browser/Device info
  last_activity = models.DateTimeField(auto_now=True)
  is_active = models.BooleanField(default=True)

  def __str__(self):
      return f"{self.user.username} session ({self.ip_address})"
  

class ScopedToken(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
  token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
  scope = models.CharField(max_length=50) # e.g., "readonly", "write_notes", "admin_access"
  expires_at = models.DateTimeField()
  is_revoked = models.BooleanField(default=False)



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
  

class UserLog(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  group = models.CharField(max_length=20) # admin or user
  action = models.TextField()
  timestamp = models.DateTimeField(auto_now_add=True)
  is_suspicious = models.BooleanField(default=False)




