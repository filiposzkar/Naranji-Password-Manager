credentials_list = []
notes_list = []
id_credentials = 1
id_notes = 1


def add_credential(new_credential):
  global id_credentials 
  new_credential['id'] = id_credentials
  credentials_list.append(new_credential)
  id_credentials = id_credentials + 1
  return new_credential


def get_all_credentials():
  return credentials_list


def get_credential_by_id(given_id):
  for item in credentials_list:
    if item['id'] == given_id:
      return item
  return None


def delete_credential(given_id):
  global credentials_list
  for item in credentials_list:
    if item['id'] == given_id:
      credentials_list.remove(item)
      return True
  return False


def update_credential(cred_id, new_data):
  for item in credentials_list:
    if item["id"] == cred_id:
      item.update(new_data)  # update() merges the new data into the old dictionary
      item['id'] = cred_id
      return item
  return None


def add_note(new_note):
  global id_notes
  
  new_note['id'] = id_notes
  print("THIS IS THE NEW NOTE: ", new_note)
  notes_list.append(new_note)
  id_notes = id_notes + 1
  return new_note


def get_note_by_id(given_id):
  for item in notes_list:
    if item['id'] == given_id:
      return item
  return None


def get_all_notes():
  return notes_list


def delete_note(given_id):
    global notes_list
    for item in notes_list:
        if item['id'] == given_id:
            notes_list.remove(item)
            return True 
    return False         


def update_note(note_id, new_data):
  for item in notes_list:
    if item["id"] == note_id:
      item.update(new_data)  # update() merges the new data into the old dictionary
      return item
  return None




