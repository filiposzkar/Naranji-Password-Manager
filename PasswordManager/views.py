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

from .models import Credential, Note
from django.db.models import Count



@csrf_exempt
def get_credentials(request):
    all_credentials = Credential.objects.all()
    serializer = CredentialSerializer(all_credentials, many=True)
    return JsonResponse({"credentials": serializer.data}, safe=False)


@csrf_exempt
def get_notes(request):
    all_notes = Note.objects.all()
    serializer = SecuredNotesSerializer(all_notes, many=True)
    return JsonResponse({"notes": serializer.data}, safe=False)


def home(request):
  return render(request, 'manager/index.html')

def notes_page(request):
  return render(request, 'manager/secretNotes.html')


@csrf_exempt 
def add_credential_view(request):
  if request.method == "POST":
    try:
        data = json.loads(request.body)  # parsing the incoming JSON
        serializer = CredentialSerializer(data=data) # giving the data to the serializer
        if serializer.is_valid():
          new_credential = serializer.save()  # performs the SQL insert into the database
          return JsonResponse(CredentialSerializer(new_credential).data, status=201) # returning the data as JSON
        else:
          return JsonResponse({"error": serializer.errors}, status=400)
    except json.JSONDecodeError:
      return JsonResponse({"error": "Invalid JSON format"}, status=400)
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
  if request.method == "POST":
    try:
        data = json.loads(request.body)  # parsing the incoming JSON
        serializer = SecuredNotesSerializer(data=data) # giving the data to the serializer
        if serializer.is_valid():
          new_note = serializer.save()  # performs the SQL insert into the database
          return JsonResponse(SecuredNotesSerializer(new_note).data, status=201) # returning the data as JSON
        else:
          return JsonResponse({"error": serializer.errors}, status=400)
    except json.JSONDecodeError:
      return JsonResponse({"error": "Invalid JSON format"}, status=400)
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
      data = Credential.objects.all() # fetch from database

      website_filter = request.query_params.get('website_name')
      if website_filter:
        data = data.filter(website_name__icontains=website_filter)

      page = int(request.query_params.get('page', 1))  # if they don't provide a page number, it returns page 1 by default; we use int because data returned by a URL is always a string
      page_size = int(request.query_params.get('page_size', 5))  # how many items are we showing on a page (in this case 5)
      start = (page - 1) * page_size # ex: if we are on page 1 -> (1 - 1) * 5 = 0, so start = 0 and end = 5 => getting items 0 through 4
      end = start + page_size

      paginated_data = data[start:end]  # getting only the elements from the list between the start and end positions

      serializer = CredentialSerializer(paginated_data, many=True) # since JavaScript and Python cannot communicate directly, we need a serializer, which converts the Python objects into JSON; many = True is indicating that we are giving a list of elements, not just one
      return Response({"count": data.count(), "results": serializer.data}) # count shows how many credentials we have in the list of credentials, results shows what credentials we have on a single page
    

    def post(self, request):
      serializer = CredentialSerializer(data=request.data) # request.data is the credential given by the user (through the HTML elements); it arrives as JSON
      if serializer.is_valid(): # we call the serializer to see if the given credential is valid and respects the attributes
          new_credential = serializer.save() # we are adding a "clean" version of the data
          return Response(CredentialSerializer(new_credential).data, status=status.HTTP_201_CREATED) # signaling success, a new credential was created and saved
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) # the given data was wrong, so we signal failure
    


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
        return Response(CredentialSerializer(updated_item).data)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
      success = service.delete_credential(pk)
      if success:
        return Response(status=status.HTTP_204_NO_CONTENT)
      return Response({"error": "Already deleted or never existed"}, status=status.HTTP_404_NOT_FOUND)    
    

@method_decorator(csrf_exempt, name='dispatch')
class NotesListCreateView(APIView):
  def get(self, request):
    data = Note.objects.all()

    headline_filter = request.query_params.get('headline')
    if headline_filter:
      data = data.filter(headline__icontains=headline_filter)

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 5))
    start = (page - 1) * page_size
    end = start + page_size

    paginated_data = data[start:end]

    serializer = SecuredNotesSerializer(paginated_data, many=True)
    return Response({"count": data.count(), "results": serializer.data})
  
  def post(self, request):
    serializer = SecuredNotesSerializer(data=request.data)
    if serializer.is_valid():
      new_note = serializer.save()
      return Response(SecuredNotesSerializer(new_note).data, status=status.HTTP_201_CREATED)
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
      return Response(SecuredNotesSerializer(updated_item).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  

  def delete(self, request, pk):
    success = service.delete_note(pk)
    if success:
      return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"error": "Already deleted or never existed"}, status=status.HTTP_404_NOT_FOUND)   


# def database_statistics(request):
#     data = {
#         "total_credentials": Credential.objects.count(),
#         "total_notes": Note.objects.count()
#     }
#     return JsonResponse(data)


def api_statistics(request):
    cred_count = Credential.objects.count()
    note_count = Note.objects.count()
    
    return JsonResponse({
        "labels": ["Credentials", "Notes"],
        "values": [cred_count, note_count]
    })




