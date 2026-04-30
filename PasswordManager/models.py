from django.db import models
from django.conf import settings

class Credential(models.Model):
  website_name = models.CharField(max_length=100)
  email = models.EmailField()
  username = models.CharField(max_length=100)
  password = models.CharField(max_length=255)
  url = models.URLField()
  logo = models.CharField(max_length=255, null=True, blank=True)

  def __str__(self):
    return f"{self.website_name} - {self.username}"
  

class Note(models.Model):
  headline = models.CharField(max_length=200)
  bodytext = models.TextField()
  logo = models.CharField(max_length=255, default="manager/assets/NotesIcon.png")
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.headline



