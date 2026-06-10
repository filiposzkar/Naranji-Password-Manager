from rest_framework import serializers
from .models import Credential, Note

class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credential
        fields = '__all__'
        read_only_fields = ['user']  # the frontend is not allowed to change the user when it sends data back, only to read it, preventing a malicious attack

class SecuredNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'
        read_only_fields = ['user']