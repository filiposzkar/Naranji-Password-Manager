import graphene 
from graphene_django import DjangoObjectType
from . import service

class CredentialType(graphene.ObjectType):
  id = graphene.Int()
  website_name = graphene.String()
  email = graphene.String()
  username = graphene.String()
  password = graphene.String()
  url = graphene.String()
  logo = graphene.String()


class NoteType(graphene.ObjectType):
  id = graphene.Int()
  logo = graphene.String()
  headline = graphene.String()
  bodytext = graphene.String()


# these are the queries (the "GET" logic)
class Query(graphene.ObjectType):
  credential = graphene.Field(CredentialType, id=graphene.Int())
  note = graphene.Field(NoteType, id=graphene.Int())
  all_credentials = graphene.List(CredentialType)
  all_notes = graphene.List(NoteType)

  def resolve_credential(root, info, id):
    return service.get_credential_by_id(id)
  
  def resolve_note(root, info, id):
    return service.get_note_by_id(id)

  def resolve_all_credentials(root, info):
    return service.get_all_credentials()
  
  def resolve_all_notes(root, info):
    return service.get_all_notes()
  

# these are the mutations (the "POST/PUT/DELETE" logic)
class CreateCredential(graphene.Mutation):
  class Arguments:
    website_name = graphene.String(required=True)
    password = graphene.String(required=True)
    username = graphene.String()
    email = graphene.String()
    url = graphene.String()
  
  credential = graphene.Field(CredentialType) # what the mutation returns

  def mutate(root, info, website_name, password, username, email, url):
    new_data = {
      "website_name": website_name,
      "password": password,
      "username": username,
      "email": email,
      "url": url
    }
    added_item = service.add_credential(new_data)
    return CreateCredential(credential=added_item)
  

class DeleteCredential(graphene.Mutation):
  class Arguments:
    id = graphene.Int(required=True)

  success = graphene.Boolean()  

  def mutate(root, info, id):
    result = service.delete_credential(id)
    return DeleteCredential(success=result)
  

class UpdateCredential(graphene.Mutation):
  class Arguments:
    id = graphene.Int(required=True)
    website_name = graphene.String(required=True)
    password = graphene.String(required=True)
    username = graphene.String()
    email = graphene.String()
    url = graphene.String()
  
  credential = graphene.Field(CredentialType) 

  def mutate(root, info, id, website_name, password, username, email, url):
    updated_data = {
      "website_name": website_name,
      "password": password,
      "username": username,
      "email": email,
      "url": url
    }
    updated_item = service.update_credential(id, updated_data)
    return UpdateCredential(credential=updated_item)
  

class CreateNote(graphene.Mutation):
  class Arguments:
    headline = graphene.String()
    bodytext = graphene.String()

  note = graphene.Field(NoteType)

  def mutate(root, info, headline, bodytext):
    new_note = {
      "headline": headline,
      "bodytext": bodytext
    }
    added_item = service.add_note(new_note)
    return CreateNote(note=added_item)
  

class DeleteNote(graphene.Mutation):
  class Arguments:
    id = graphene.Int(required=True)

  success = graphene.Boolean()  

  def mutate(root, info, id):
    result = service.delete_note(id)
    return DeleteNote(success=result)


class UpdateNote(graphene.Mutation):
  class Arguments:
    id = graphene.Int(required=True)
    headline = graphene.String()
    bodytext = graphene.String()
  
  note = graphene.Field(NoteType) 

  def mutate(root, info, id, headline, bodytext):
    updated_data = {
      "headline": headline,
      "bodytext": bodytext,
    }
    updated_item = service.update_note(id, updated_data)
    return UpdateNote(note=updated_item)


class Mutation(graphene.ObjectType):
    create_credential = CreateCredential.Field()   # create_credential is the name the frontend will use to call the function
    delete_credential = DeleteCredential.Field()
    update_credential = UpdateCredential.Field()

    create_note = CreateNote.Field()
    delete_note = DeleteNote.Field()
    update_note = UpdateNote.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)  # the master map, combining the query branch and mutation branch

  


  

  
 