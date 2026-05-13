from django.shortcuts import render, redirect
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
from .models import Credential, Note, CustomUser, UserLog, Role
from django.db.models import Count
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.views.decorators.csrf import ensure_csrf_cookie
from .service import record_user_action
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings


@login_required
def get_credentials(request):
    user_credentials = Credential.objects.filter(user=request.user).order_by('-id')
    serializer = CredentialSerializer(user_credentials, many=True)
    return JsonResponse(serializer.data, safe=False) 

@login_required
def get_notes(request):
    user_notes = Note.objects.filter(user=request.user).order_by('-id')
    serializer = SecuredNotesSerializer(user_notes, many=True)
    return JsonResponse(serializer.data, safe=False)


def home(request):
  return render(request, 'manager/index.html')

def notes_page(request):
  return render(request, 'manager/secretNotes.html')

# def statistics_page(request):
#   return render(request, 'manager/statistics.html')

@login_required
def statistics_page(request):
  if not request.user.is_superuser and not (request.user.role and request.user.role.name == "Admin"):
      return redirect('home')

  suspicious_logs = UserLog.objects.filter(is_suspicious=True).order_by('-timestamp')

  return render(request, 'manager/statistics.html', {
      'suspicious_logs': suspicious_logs
  })

def login_view(request):
    if request.method == "POST":
      u = request.POST.get('username')
      p = request.POST.get('password')

      user = authenticate(request, username=u, password=p) # Django checks the hashed password automatically
      if user is not None:
        login(request, user)
        return redirect('home') # sending the user to the credentials list
      else:
         messages.error(request, "Invalid username or password!")
    
    return render(request, 'manager/login.html')


def register_view(request):
  if request.method == "POST":
    try:
      data = json.loads(request.body)
      username = data.get('username')
      email = data.get('email')
      password = data.get('password')

      if CustomUser.objects.filter(username=username).exists(): # validation
        return JsonResponse({"error": "Username already exists"}, status=400)
      
      default_role = Role.objects.filter(name="Normal User").first()

      new_user = CustomUser.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=default_role
      )
      return JsonResponse({"message": "Registration successful!"}, status=201)

    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
  
  return render(request, 'manager/signUp.html')
      



@ensure_csrf_cookie
@login_required
def index(request):
    if request.user.is_superuser or request.user.role.name == "Admin":  # fetch the credentials based on role
        credentials = Credential.objects.all()  # admins see everything in the system
    else:
        credentials = Credential.objects.filter(user=request.user) # normal users only see their own credentials
    return render(request, 'index.html', {'credentials': credentials})


def chat_view(request):
  return render(request, 'manager/chat.html')    


def get_crypto_key(master_key_string):  # turns the user's master key string into a 32-byte URL-safe base64 key
  password = master_key_string.encode()

  # A 'salt' is used to ensure the same password results in different keys elsewhere.
  salt = b'lab_project_salt_123'
  kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
  )
  return base64.urlsafe_b64encode(kdf.derive(password))


def add_credential_view(request):
  if request.method == "POST":
    try:
        master_key = request.headers.get('X-Master-Key')  # extracting the master key from the custom header
        if not master_key:
          return JsonResponse({"error": "Master key is required for encryption"}, status=400)
        
        data = json.loads(request.body)  # parsing the incoming JSON

        # encrypting the password
        raw_password = data.get('password')
        if raw_password:
          key = get_crypto_key(master_key)
          f = Fernet(key)
          encrypted_password = f.encrypt(raw_password.encode()).decode()
          data['password'] = encrypted_password

        serializer = CredentialSerializer(data=data) # giving the data to the serializer
        if serializer.is_valid():
          new_credential = serializer.save(user=request.user)
          return JsonResponse(CredentialSerializer(new_credential).data, status=201) # returning the data as JSON
        else:
          return JsonResponse({"error": serializer.errors}, status=400)
        
    except json.JSONDecodeError:
      return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
  return JsonResponse({"error": "Only POST allowed"}, status=405)
         
         

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



def add_note_view(request):
  # raise Exception("IF YOU SEE THIS, THE CODE IS WORKING")
  if request.method == "POST":
    data = json.loads(request.body)  # parsing the incoming JSON
    serializer = SecuredNotesSerializer(data=data) # giving the data to the serializer
    if serializer.is_valid():
      new_note = serializer.save(user=request.user)
      print("!!! TEST: I AM ABOUT TO LOG !!!")
      return JsonResponse(SecuredNotesSerializer(new_note).data, status=201) # returning the data as JSON
    else:
      return JsonResponse({"error": serializer.errors}, status=400)
  return JsonResponse({"error": "Only POST allowed"}, status=405)



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



class CredentialListCreateView(APIView):  # this is for when we talk to all the credentials, and we dont need an ID
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
      data = Credential.objects.filter(user=request.user).order_by('-id')

      website_filter = request.query_params.get('website_name')
      if website_filter:
        data = data.filter(website_name__icontains=website_filter)

      page = int(request.query_params.get('page', 1))  # if they don't provide a page number, it returns page 1 by default; we use int because data returned by a URL is always a string
      page_size = int(request.query_params.get('page_size', 10))  # how many items are we showing on a page (in this case 5)
      start = (page - 1) * page_size # ex: if we are on page 1 -> (1 - 1) * 5 = 0, so start = 0 and end = 5 => getting items 0 through 4
      end = start + page_size

      paginated_data = data[start:end]  # getting only the elements from the list between the start and end positions

      # Decryption step
      master_key = request.headers.get('X-Master-Key')
      if master_key:
        try:
          f = Fernet(get_crypto_key(master_key))
          for item in paginated_data:
            if item.password.startswith('gAAAAA'):
                decrypted_val = f.decrypt(item.password.encode()).decode()
                item.password = decrypted_val

        
        except Exception as e:
          print(f"Decryption error: {e}") 
          return Response({"error": "Invalid Master Key!"}, status=401)
      
      serializer = CredentialSerializer(paginated_data, many=True) # since JavaScript and Python cannot communicate directly, we need a serializer, which converts the Python objects into JSON; many = True is indicating that we are giving a list of elements, not just one
      return Response({"count": data.count(), "results": serializer.data}) # count shows how many credentials we have in the list of credentials, results shows what credentials we have on a single page
    
    
    def post(self, request):
      master_key = request.headers.get('X-Master-Key')
      if not master_key:
        return Response({"error": "Master Key required for encryption"}, status=400)

      serializer = CredentialSerializer(data=request.data)
      if serializer.is_valid():
        try:
          # encrypting the password before it hits the database
          crypto_key = get_crypto_key(master_key)
          f = Fernet(crypto_key)
          
          # getting the plain text from the serializer's data
          plain_password = serializer.validated_data['password']
          encrypted_password = f.encrypt(plain_password.encode()).decode()

          # overwriting the password with the encrypted version during save
          new_credential = serializer.save(
            user=request.user,
            password = encrypted_password
          )
          new_credential.password = plain_password
          response_serializer = CredentialSerializer(new_credential)
          record_user_action(request.user, f"Created new credential: {new_credential}")
          return Response(serializer.data, status=status.HTTP_201_CREATED)
      
        except Exception as e:
          return Response({"error": f"Encryption failed: {str(e)}"}, status=500)
        
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


method_decorator(csrf_exempt, name='dispatch')
class CredentialDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
      credential = service.get_credential_by_id(pk)
      if credential is not None:
        if credential.user != request.user:
          return Response({"error": "Unauthorized"}, status=403)

        master_key = request.headers.get('X-Master-Key')
        if master_key:
          try:
            f = Fernet(get_crypto_key(master_key))
            credential.password = f.decrypt(credential.password.encode()).decode()
          except Exception:
            return Response({"error": "Decryption failed"}, status=401)

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
        record_user_action(request.user, f"Updated credential: {updated_item.website_name}")
        return Response(CredentialSerializer(updated_item).data)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
      credential = service.get_credential_by_id(pk)
      credential_website = credential.website_name if credential else "Unknown"
      success = service.delete_credential(pk)
      if success:
        record_user_action(request.user, f"Deleted Credential: {credential_website}")
        return Response(status=status.HTTP_204_NO_CONTENT)
      return Response({"error": "Already deleted or never existed"}, status=status.HTTP_404_NOT_FOUND)  

    


class NotesListCreateView(APIView):
  authentication_classes = [SessionAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request):
    data = Note.objects.filter(user=request.user).order_by('-id')

    headline_filter = request.query_params.get('headline')
    if headline_filter:
      data = data.filter(headline__icontains=headline_filter)

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    start = (page - 1) * page_size
    end = start + page_size

    paginated_data = data[start:end]

    master_key = request.headers.get('X-Master-Key')
    if master_key:
      try:
        f = Fernet(get_crypto_key(master_key))
        for note in paginated_data:
          if note.bodytext.startswith('gAAAAA'):
            decrypted_val = f.decrypt(note.bodytext.encode()).decode()
            note.bodytext = decrypted_val
      except Exception as e:
        print(f"Decryption error: {e}")
        return Response({"error": "Invalid Master Key!"}, status=401)

    serializer = SecuredNotesSerializer(paginated_data, many=True)
    return Response({"count": data.count(), "results": serializer.data})
  


  def post(self, request):
    master_key = request.headers.get('X-Master-Key')
    if not master_key:
      return Response({"error": "Master Key required"}, status=400)
    
    serializer = SecuredNotesSerializer(data=request.data)
    if serializer.is_valid():
      try:
        crypto_key = get_crypto_key(master_key)
        f = Fernet(crypto_key)
        
        plain_content = serializer.validated_data['bodytext']
        encrypted_content = f.encrypt(plain_content.encode()).decode()

        new_note = serializer.save(user=request.user, bodytext=encrypted_content)
        
        new_note.bodytext = plain_content
        response_serializer = SecuredNotesSerializer(new_note)

        record_user_action(request.user, f"Created new note: {new_note}")
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
      
      except Exception as e:
        return Response({"error": f"Encryption failed: {str(e)}"}, status=500)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  


method_decorator(csrf_exempt, name='dispatch')
class NotesDetailView(APIView):
  authentication_classes = [SessionAuthentication]
  permission_classes = [IsAuthenticated]

  def get(self, request, pk):
    note = service.get_note_by_id(pk)
    if note is None:
      return Response({"error": "Note not found"}, status=404)

    master_key = request.headers.get('X-Master-Key')
    if master_key and note.bodytext.startswith('gAAAAA'):
      try:
        f = Fernet(get_crypto_key(master_key))
        note.bodytext = f.decrypt(note.bodytext.encode()).decode()
      except:
        return Response({"error": "Decryption failed"}, status=401)

    serializer = SecuredNotesSerializer(note)
    return Response(serializer.data)


  def put(self, request, pk):
    master_key = request.headers.get('X-Master-Key')
    if not master_key:
        return Response({"error": "Master Key required"}, status=400)

    existing_item = service.get_note_by_id(pk)
    if existing_item is None:
        return Response({"error": "Not found"}, status=404)
    
    serializer = SecuredNotesSerializer(data=request.data)
    if serializer.is_valid():
      try:
        f = Fernet(get_crypto_key(master_key))
        plain_content = serializer.validated_data['bodytext']
        encrypted_content = f.encrypt(plain_content.encode()).decode()

        validated_data = serializer.validated_data
        validated_data['bodytext'] = encrypted_content
        
        updated_item = service.update_note(pk, validated_data)
        
        updated_item.bodytext = plain_content
        record_user_action(request.user, f"Updated note: {updated_item.headline}")
        return Response(SecuredNotesSerializer(updated_item).data)
      
      except Exception as e:
        return Response({"error": str(e)}, status=500)
            
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  

  def delete(self, request, pk):
    note = service.get_note_by_id(pk)
    note_headline = note.headline if note else "Unknown"
    success = service.delete_note(pk)
    if success:
      record_user_action(request.user, f"Deleted Note: {note_headline}")
      return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"error": "Already deleted or never existed"}, status=status.HTTP_404_NOT_FOUND)   


def api_statistics(request):
  cred_count = Credential.objects.count()
  note_count = Note.objects.count()
  
  return JsonResponse({
      "labels": ["Credentials", "Notes"],
      "values": [cred_count, note_count]
  })


def api_security_stats(request): # counting how many total logs are clean vs. flagged
  suspicious_count = UserLog.objects.filter(is_suspicious=True).count()
  safe_count = UserLog.objects.filter(is_suspicious=False).count()
  
  return JsonResponse({
    "labels": ["Safe Actions", "Suspicious Actions"],
    "values": [safe_count, suspicious_count],
    "colors": ["#a4c639", "#d9534f"]
  })


@login_required
def observation_list(request):  # this functions displays the suspicious events
  if not request.user.is_superuser and not request.user.role.name == "Admin":
    return redirect('home')

  suspicious_logs = UserLog.objects.filter(is_suspicious=True).order_by('-timestamp')

  return render(request, 'manager/statistics.html', {
    'suspicious-logs': suspicious_logs
  })
   




