from .models import Credential, Note


def add_credential(data):
  serializer = CredentialSerializer(data=data)
  if serializer.is_valid():
      return serializer.save() # returns the model object
  return None

def get_all_credentials(data):
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

def get_all_notes(data):
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





