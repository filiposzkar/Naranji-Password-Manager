from .models import Credential, Note, UserLog
from .serializers import CredentialSerializer, SecuredNotesSerializer
from django.utils import timezone
from datetime import timedelta


def add_credential(data):
  serializer = CredentialSerializer(data=data)
  if serializer.is_valid():
      return serializer.save() # return the created database object
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
    serializer = CredentialSerializer(credential, data=new_data, partial=True)
    if serializer.is_valid():
      return serializer.save()  
  return None




def add_note(data):
  serializer = SecuredNotesSerializer(data=data)
  if serializer.is_valid():
      return serializer.save()
  return None

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
    serializer = SecuredNotesSerializer(note, data=new_data, partial=True)
    if serializer.is_valid():
      return serializer.save()
  return None


def record_user_action(user, action_description):
  try:
    if not user or not user.is_authenticated:    # rejecting anonymous or not logged-in users
      print("LOGGING ABORTED: User is not authenticated.")
      return False


    # what label to put in the log
    group_name = "User"
    if user.is_superuser:
      group_name = "Admin (Superuser)"
    elif hasattr(user, 'role') and user.role:
      group_name = user.role.name
    

    # creating the new database entry for this log
    new_log = UserLog.objects.create(
      user=user,
      group=group_name,
      action=action_description,
      is_suspicious=False 
    )
    print(f"LOG PERSISTED: ID {new_log.id}")


    # checking for more than 5 actions in the last 30 seconds
    time_window = timezone.now() - timedelta(seconds=30)
    recent_activity_count = UserLog.objects.filter(      # how many logs exist for this specific user in 30 seconds
      user=user,
      timestamp__gte=time_window
    ).count()
    print(f"RECENT ACTIVITY LEVEL: {recent_activity_count} actions/30s")


    if recent_activity_count > 5:  # if the User completed more than 5 actions in 30 seconds, they are suspicious
      UserLog.objects.filter(user=user).update(is_suspicious=True)
      print(f"ALERT: {user.username} FLAGGED FOR SUSPICIOUS ACTIVITY!")
      return True 

  except Exception as e:
    print(f"CRITICAL LOGGER FAILURE: {str(e)}")
  
  return False