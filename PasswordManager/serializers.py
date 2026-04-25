from rest_framework import serializers

class CredentialSerializer(serializers.Serializer):
  id = serializers.IntegerField(read_only=True)
  website_name = serializers.CharField(max_length=300, required=True)
  url = serializers.URLField(max_length=300)
  username = serializers.CharField(max_length=300)
  email = serializers.EmailField(max_length=300)
  password = serializers.CharField(max_length=300)


class SecuredNotesSerializer(serializers.Serializer):
  id = serializers.IntegerField(read_only=True)
  headline = serializers.CharField(max_length = 300, default = "New Note")
  bodytext = serializers.CharField()