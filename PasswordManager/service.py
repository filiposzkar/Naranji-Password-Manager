from .models import Credential, Note, UserLog
from .serializers import CredentialSerializer, SecuredNotesSerializer
from django.utils import timezone
from datetime import timedelta


def add_credential(data):
  serializer = CredentialSerializer(data=data)
  if serializer.is_valid():
      return serializer.save() # returns the model object
  return None

def get_all_credentials():
  return Credential.objects.all()

def get_credential_by_id(given_id):
  try:
    return Credential.objects.get(id=given_id)
  except Credential.DoesNotExist:
    return None
  
def delete_credential(given_id):
  credential = get_credential_by_id(given_id)
  if credential:
    credential.delete()
    return True
  return False

def update_credential(cred_id, new_data):
  credential = get_credential_by_id(cred_id)
  if credential:
    for attr, value in new_data.items():
      setattr(credential, attr, value)
    credential.save()
    return credential
  return None



def add_note(data):
  return Note.objects.create(**data)

def get_all_notes():
  return Note.objects.all()

def get_note_by_id(given_id):
  try:
    return Note.objects.get(id=given_id)
  except Note.DoesNotExist:
    return None

def delete_note(given_id):
  note = get_note_by_id(given_id)
  if note:
    note.delete()
    return True
  return False

def update_note(note_id, new_data):
  note = get_note_by_id(note_id)
  if note:
    for attr, value in new_data.items():
      setattr(note, attr, value)
    note.save()
    return note
  return None


def record_user_action(user, action_description):
  user_role = user.role.name if user.role else "No Role"  # grabbing the role name from the CustomUser model

  new_log = UserLog.objects.create(  # creating the new log entry
    user = user,
    group = user_role, # GROUP_ID[ADMIN/USER] requirement
    action = action_description
  )

  # we need to define what a suspicious user behavior looks like
  # if the user performs more than 10 actions in 30 seconds => sus
  time_threshold = timezone.now() - timedelta(seconds=30)  
  recent_actions = UserLog.objects.filter(
    user = user,
    timestamp__gte = time_threshold
  ).count()

  if recent_actions > 10:
    UserLog.objects.filter(user=user).update(is_suspicious=True)
    return True # signaling that something is wrong
  return False









