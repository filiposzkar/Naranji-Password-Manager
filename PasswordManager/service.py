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


# def record_user_action(user, action_description):
#   print(f"DEBUG: Attempting to log action for {user}: {action_description}") 
#   user_role = user.role.name if user.role else "No Role"  # grabbing the role name from the CustomUser model

#   new_log = UserLog.objects.create(  # creating the new log entry
#     user = user,
#     group = user_role, # GROUP_ID[ADMIN/USER] requirement
#     action = action_description
#   )
#   print(f"DEBUG: Log created with ID: {new_log.id}") 

#   # we need to define what a suspicious user behavior looks like
#   # if the user performs more than 10 actions in 30 seconds => sus
#   time_threshold = timezone.now() - timedelta(seconds=30)  
#   recent_actions = UserLog.objects.filter(
#     user = user,
#     timestamp__gte = time_threshold
#   ).count()

#   if recent_actions > 5:
#     UserLog.objects.filter(user=user).update(is_suspicious=True)
#     return True # signaling that something is wrong
#   return False



def record_user_action(user, action_description):
    try:
        # 2. Safety Check: Anonymous users cannot be logged in this model
        if not user or not user.is_authenticated:
            print("❌ LOGGING ABORTED: User is not authenticated.")
            return False

        # 3. Dynamic Group Identification (Prevents crashes if role is missing)
        group_name = "User" # Default
        if user.is_superuser:
            group_name = "Admin (Superuser)"
        elif hasattr(user, 'role') and user.role:
            group_name = user.role.name
        
        # 4. Create the Database Entry
        new_log = UserLog.objects.create(
            user=user,
            group=group_name,
            action=action_description,
            is_suspicious=False  # Initial state
        )
        print(f"✅ LOG PERSISTED: ID {new_log.id}")

        # 5. Malvolent Behavior Detection (The 'Stealth' Logic)
        # Check for more than 5 actions (for testing) in the last 30 seconds
        time_window = timezone.now() - timedelta(seconds=30)
        recent_activity_count = UserLog.objects.filter(
            user=user,
            timestamp__gte=time_window
        ).count()

        print(f"📊 RECENT ACTIVITY LEVEL: {recent_activity_count} actions/30s")

        if recent_activity_count > 5:
            # Flag ALL logs for this user as suspicious for Admin review
            UserLog.objects.filter(user=user).update(is_suspicious=True)
            print(f"🚨 ALERT: {user.username} FLAGGED FOR SUSPICIOUS ACTIVITY!")
            return True # Signal that detection triggered

    except Exception as e:
        # This will catch missing tables, column mismatches, or logic errors
        print(f"🔥 CRITICAL LOGGER FAILURE: {str(e)}")
    
    return False