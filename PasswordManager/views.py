from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CredentialSerializer
from .serializers import SecuredNotesSerializer
from . import service
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json


credentials_list = [
  {"id": 1, "website_name": "Figma", "email": "filiposcar1616@gmail.com", "username": "Filip Oszkar", "password": "abc", "url": "www.figma.com", "logo": "figma.png"},
  {"id": 2, "website_name": "Facebook", "email": "filiposcar1616@gmail.com", "username": "Filip Oszkar", "password": "abc", "url": "www.facebook.com", "logo": "facebook.png"},
]

notes_list = [
  {"id": 1, "logo": "NotesIcon.png", "headline": "Project Ideas", "bodytext": "Lorem ipsum"},
  {"id": 2, "logo": "NotesIcon.png", "headline": "Lecture notes", "bodytext": "Lorem ipsum 2"},
]

def get_credentials(request):
  return JsonResponse({"credentials": credentials_list}, safe=False)

def get_notes(request):
  return JsonResponse({"notes": notes_list}, safe=False)

def home(request):
  return render(request, 'manager/index.html')

def notes_page(request):
  return render(request, 'manager/secretNotes.html')

@csrf_exempt
def add_credential_view(request):
    print(f"--- DEBUG DATA: {request.body} ---")

    data = json.loads(request.body)
    print(f"DEBUG - Website: {data.get('website_name')}")
    print(f"DEBUG - Password: {data.get('account_password')}")
    print(f"DEBUG - Does 'password' key exist? {'password' in data}")
    if request.method == "POST":
        try:
            
            data = json.loads(request.body)
            
            website = data.get('website_name')
            username = data.get('username')
            password = data.get('password')

            if not website or not password:
                return JsonResponse({"error": "Missing required fields: website_name and password"}, status=400)

            
            new_entry = {
                "id": len(credentials_list) + 1,
                "website_name": website,
                "url": data.get('url'), 
                "username": data.get('username'), 
                "email": data.get('email'),
                "password": password,
                "logo": data.get('logo')
            }
            new_entry = service.add_credential(data)

            return JsonResponse(new_entry, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST allowed"}, status=405)


@csrf_exempt
def update_credential_view(request, cred_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            website = data.get('website_name')
            password = data.get('password')

            if website == "" or password == "":
                return JsonResponse({"error": "Fields website_name and password cannot be empty"}, status=400)

            updated_item = service.update_credential(cred_id, data)

            if updated_item:
                return JsonResponse(updated_item, status=200)
            else:
                return JsonResponse({"error": "Credential not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only PUT allowed"}, status=405)




@csrf_exempt
def delete_credential_view(request, cred_id):
    if request.method == "DELETE":
        try:
            success = service.delete_credential(cred_id)
            
            if success:
                return JsonResponse({"message": "Deleted successfully"}, status=200)
            else:
                return JsonResponse({"error": "Credential not found"}, status=404)
                
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only DELETE allowed"}, status=405)



@csrf_exempt
def add_note_view(request):
    print(f"--- DEBUG DATA: {request.body} ---")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            title = data.get('headline')
            content = data.get('bodytext')

            if not title or not content:
                return JsonResponse({"error": "Missing required fields: headline and bodytext"}, status=400)

            new_entry = {
               "id": len(notes_list) + 1,
               "logo": "manager/assets/NotesIcon.png",
               "headline": data.get('headline'),
               "bodytext": data.get('bodytext')
            }
            new_entry = service.add_note(data)

            print(f"DEBUG: Current notes in RAM: {service.notes_list}")

            return JsonResponse(new_entry, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST allowed"}, status=405) 


@csrf_exempt
def update_note_view(request, cred_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            headline = data.get('headline')
            bodytext = data.get('bodytext')

            if headline == "" or bodytext == "":
              return JsonResponse({"error": "Fields headline and bodytext cannot be empty"}, status=400)

            updated_item = service.update_note(cred_id, data)

            if updated_item:
                return JsonResponse(updated_item, status=200)
            else:
                return JsonResponse({"error": "Note not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only PUT allowed"}, status=405)


@csrf_exempt
def delete_note_view(request, note_id):
    if request.method == "DELETE":
        try:
            success = service.delete_note(note_id)
            
            if success:
                return JsonResponse({"message": "Deleted successfully"}, status=200)
            else:
                return JsonResponse({"error": "Note not found"}, status=404)
                
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only DELETE allowed"}, status=405)



@method_decorator(csrf_exempt, name='dispatch')
class CredentialListCreateView(APIView):  # this is for when we talk to all the credentials, and we dont need an ID
    # displaying all the credentials (or a part of it)
    def get(self, request):
      data = service.get_all_credentials()

      # Reading the user's request
      page = int(request.query_params.get('page', 1))  # if they don't provide a page number, it returns page 1 by default; we use int because data returned by a URL is always a string
      page_size = int(request.query_params.get('page_size', 5))  # how many items are we showing on a page (in this case 5)
      start = (page - 1) * page_size # ex: if we are on page 1 -> (1 - 1) * 5 = 0, so start = 0 and end = 5 => getting items 0 through 4
      end = start + page_size

      paginated_data = data[start:end]  # getting only the elements from the list between the start and end positions

      serializer = CredentialSerializer(paginated_data, many=True) # since JavaScript and Python cannot communicate directly, we need a serializer, which converts the Python objects into JSON; many = True is indicating that we are giving a list of elements, not just one
      return Response({"count": len(data), "results": serializer.data}) # count shows how many credentials we have in the list of credentials, results shows what credentials we have on a single page
    

    # adding a new credential to the list
    # we use this function in order to determine if it's safe to save the new credential received from JavaScript into our Python list
    # def post(self, request):
    #   serializer = CredentialSerializer(data=request.data)  # request.data is the credential given by the user (through the HTML elements); it arrives as JSON
    #   if serializer.is_valid(): # we call the serializer to see if the given credential is valid and respects the attributes
    #     new_credential = service.add_credential(serializer.validated_data) # we are adding a "clean" version of the data
    #     return Response(new_credential, status=status.HTTP_201_CREATED)  # signaling success, a new credential was created and saved
    #   return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) # the given data was wrong, so we signal failure

    def post(self, request):
      print("DEBUG: Received data:", request.data) # Check your terminal for this!
      serializer = CredentialSerializer(data=request.data)
      if serializer.is_valid():
          new_credential = service.add_credential(serializer.validated_data)
          print("DEBUG: Saved successfully!")
          return Response(new_credential, status=status.HTTP_201_CREATED)
      
      print("DEBUG: Validation Errors:", serializer.errors) # This tells you why it failed
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@method_decorator(csrf_exempt, name='dispatch')
class CredentialDetailView(APIView):
    def get(self, request, pk):
      credential = service.get_credential_by_id(pk)
      if credential is not None:
        serializer = CredentialSerializer(credential)
        return Response(serializer.data)
      return Response({"error": "Credential not found"}, status=status.HTTP_404_NOT_FOUND)
    

    def put(self, request, pk): # updating a credential
      # checking if the credential to be updated exists
      existing_item = service.get_credential_by_id(pk)
      if existing_item is None:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
      
      # validating the new data
      serializer = CredentialSerializer(data=request.data)
      if serializer.is_valid():
        updated_item = service.update_credential(pk, serializer.validated_data)
        return Response(updated_item)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
      success = service.delete_credential(pk)
      if success:
        return Response(status=status.HTTP_204_NO_CONTENT)
      return Response({"error": "Already deleted or never existed"}, status=status.HTTP_404_NOT_FOUND)    
    

@method_decorator(csrf_exempt, name='dispatch')
class NotesListCreateView(APIView):
  def get(self, request):
    data = service.get_all_notes()

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 5))
    start = (page - 1) * page_size
    end = start + page_size

    paginated_data = data[start:end]

    serializer = SecuredNotesSerializer(paginated_data, many=True)
    return Response({"count": len(data), "results": serializer.data})
  
  def post(self, request):
    serializer = SecuredNotesSerializer(data=request.data)
    if serializer.is_valid():
      new_note = service.add_note(serializer.validated_data)
      return Response(new_note, status=status.HTTP_201_CREATED) 
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  


@method_decorator(csrf_exempt, name='dispatch')
class NotesDetailView(APIView):
  def get(self, request, pk):
    note = service.get_note_by_id(pk)
    if note is not None:
      serializer = SecuredNotesSerializer(note)
      return Response(serializer.data)
    return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)


  def put(self, request, pk):
    existing_item = service.get_note_by_id(pk)
    if existing_item is None:
      return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SecuredNotesSerializer(data=request.data)
    if serializer.is_valid():
      updated_item = service.update_note(pk, serializer.validated_data)
      return Response(updated_item)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  

  def delete(self, request, pk):
    success = service.delete_note(pk)
    if success:
      return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"error": "Already deleted or never existed"}, status=status.HTTP_404_NOT_FOUND)    


