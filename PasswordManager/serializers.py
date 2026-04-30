from rest_framework import serializers
from .models import Credential, Note

class CredentialSerializer(serializers.ModelSerializer):
  class Meta:
    model = Credential
    fields = ['id', 'website_name', 'url', 'email', 'username', 'password', 'logo']
    read_only_fields = ['id'] # important for 3NF database


class SecuredNotesSerializer(serializers.ModelSerializer):
  class Meta:
    model = Note
    fields = ['id', 'headline', 'bodytext', 'logo', 'created_at']
    read_only_fields = ['id', 'created_at']