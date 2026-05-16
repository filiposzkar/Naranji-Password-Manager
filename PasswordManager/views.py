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
from .models import Credential, Note, CustomUser, UserLog, Role, EmergencyAccessCode, RecoveryKey, ScopedToken
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
from django.shortcuts import get_object_or_404
import pyotp
import qrcode
import io
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password
import secrets, string
from django.contrib.auth.hashers import make_password
from .models import EmergencyAccessCode
from rest_framework.decorators import permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_protect
from functools import wraps
import uuid
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import PermissionDenied




def role_required(codename):
    """
    Custom decorator checking if a user has a specific permission codename
    linked to their Role before letting them access a view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
              return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)
            
            print(f"DEBUG: User '{request.user.username}' has role '{request.user.role}' and perms: {[p.codename for p in request.user.role.permissions.all()] if request.user.role else 'No Role Assigned'}")

            # calls the model's exact method: self.role.permissions.filter(codename=codename).exists()
            if not request.user.has_custom_permission(codename):
              return JsonResponse({"status": "error", "message": "Access Denied: Unauthorized role."}, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator



def check_token_scope(request, allowed_scopes):
  """
  Validates that the incoming X-Scoped-Token header matches 
  at least one of the allowed scopes string/list.
  """
  token_str = request.headers.get('X-Scoped-Token')
  if not token_str:
    raise PermissionDenied("Missing API Scoped Token.")
      
  try:
    # Resolve the token string from the database
    token_obj = ScopedToken.objects.get(
      token=uuid.UUID(token_str), 
      is_revoked=False, 
      expires_at__gt=timezone.now()
    )
    
    # if a single string was passed (e.g., "write_notes"), convert it to a list
    if isinstance(allowed_scopes, str):
      scopes_list = [allowed_scopes]
    else:
      scopes_list = allowed_scopes # If it's already a list/array
        
    # Check if the database token's scope is valid
    if token_obj.scope not in scopes_list:
      raise PermissionDenied("Token scope insufficient for this action.")
        
    return token_obj.user  # Returns the user object cleanly
      
  except (ValueError, ScopedToken.DoesNotExist):
    raise PermissionDenied("Invalid or expired token.")


def get_credentials(request):
  if request.method == "GET":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])
      user_credentials = Credential.objects.filter(user=token_user).order_by('-id')
      
      serializer = CredentialSerializer(user_credentials, many=True)
      return JsonResponse(serializer.data, safe=False, status=200)
        
    except PermissionDenied as error:
        return JsonResponse({"error": str(error)}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
          
  return JsonResponse({"error": "Only GET allowed"}, status=405)



def get_notes(request):
  if request.method == "GET":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])
      user_notes = Note.objects.filter(user=token_user).order_by('-id')
      
      serializer = SecuredNotesSerializer(user_notes, many=True)
      return JsonResponse(serializer.data, safe=False, status=200)
        
    except PermissionDenied as error:
      return JsonResponse({"error": str(error)}, status=403)
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
          
  return JsonResponse({"error": "Only GET allowed"}, status=405)



def home(request):
  return render(request, 'manager/index.html')

def notes_page(request):
  return render(request, 'manager/secretNotes.html')


@login_required
def statistics_page(request):
  if not request.user.is_superuser and not (request.user.role and request.user.role.name == "Admin"):
    return redirect('home')

  suspicious_logs = UserLog.objects.filter(is_suspicious=True).order_by('-timestamp')

  return render(request, 'manager/statistics.html', {
    'suspicious_logs': suspicious_logs
  })



@api_view(['GET', 'POST'])
def login_view(request):

  if request.method == 'GET':
    return render(request, 'manager/login.html')
  
  username = request.data.get('username')
  password = request.data.get('password')
  user = authenticate(request, username=username, password=password)
  
  if user is not None:
    if user.is_mfa_enabled:
      return Response({
        "mfa_required": True,
        "username": user.username 
      }, status=200)
    
    login(request, user)
    return Response({"mfa_required": False}, status=200)

  return Response({"error": "Invalid username or password"}, status=401)



@api_view(['POST'])
def verify_login_mfa(request):
    username = request.data.get('username')
    code = request.data.get('code')
    
    try:
        user = CustomUser.objects.get(username=username)
        
        # Helper function to generate tokens automatically on success
        def generate_user_scoped_token(authenticated_user):
          # Check permissions string dynamically from the user's database role
          if authenticated_user.role and authenticated_user.role.name == "Admin":
            token_scope = "admin_access"
          else:
            token_scope = "write_notes" # or matching scheme from your scopes list
              
          # Create the database record
          new_token = ScopedToken.objects.create(
            user=authenticated_user,
            token=uuid.uuid4(),
            scope=token_scope,
            expires_at=timezone.now() + timedelta(hours=2) # Token is active for 2 hours
          )
          return new_token


        # trying the 6-digit code first
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(code):
          login(request, user) # Existing session registration
          
          # Generate the permission scheme token!
          user_token = generate_user_scoped_token(user)
          return Response({
            "message": "Authorized",
            "token": str(user_token.token),
            "scope": user_token.scope
          }, status=200)
            

        # if MFA fails, we are trying the Emergency Recovery Code, the 10-digit code
        # looking for unused codes for this user
        recovery_codes = EmergencyAccessCode.objects.filter(user=user, used=False)
        for recovery_obj in recovery_codes:
          if check_password(code, recovery_obj.code_hash):  # checking if the code the user typed matches this stored hash
            recovery_obj.used = True  # success, so we "destroy" the code so it can't be used again
            recovery_obj.save()
            
            login(request, user) # Existing session registration
            
            # Generate the permission scheme token here too!
            user_token = generate_user_scoped_token(user)
            
            return Response({
              "message": "Authorized",
              "token": str(user_token.token),
              "scope": user_token.scope
            }, status=200)
                
        return Response({"error": "Invalid code or recovery key"}, status=401)
        
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)




@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def generate_new_codes(request):
    # 1. Secondary Gate: Enforce your custom token scope check!
    # Even if they have a session cookie, they MUST provide a valid X-Scoped-Token header.
    try:
        check_token_scope(request, ["write_notes", "admin_access"])
    except PermissionDenied as error:
        return Response({"error": str(error)}, status=403)

    # 2. Your existing logic remains completely intact and safe:
    EmergencyAccessCode.objects.filter(user=request.user).delete()
    
    raw_codes = []
    for _ in range(10):
        code = '-'.join(''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4)) for _ in range(3))
        raw_codes.append(code)
        
        EmergencyAccessCode.objects.create(
            user=request.user,
            code_hash=make_password(code)
        )
        
    return Response({'codes': raw_codes}, status=200)



def derive_key(phrase):  # this function transforms the words given by the user as recovery master key, and turns them into a strong cryptographic key
  return base64.urlsafe_b64encode(phrase.ljust(32)[:32].encode())



@api_view(['POST'])
def recover_master_key(request):
  username = request.data.get('username')
  provided_words = request.data.get('recovery_phrase').strip()

  try:
    user = CustomUser.objects.get(username=username)
    recovery_data = RecoveryKey.objects.get(user=user)
      
    if check_password(provided_words, recovery_data.recovery_phrase_hash):
      # deriving the key from the provided words
      crypto_key = derive_key(provided_words)
      f = Fernet(crypto_key)
      
      # decrypting the original master key backup
      decrypted_master_key = f.decrypt(recovery_data.encrypted_master_key_backup.encode()).decode()
      
      # return it to the frontend so the user can log in and view their data
      return Response({"master_key": decrypted_master_key}, status=200)
    else:
      return Response({"error": "Incorrect recovery phrase"}, status=401)
          
  except (CustomUser.DoesNotExist, RecoveryKey.DoesNotExist):
    return Response({"error": "Recovery data not found"}, status=404)



@login_required # ensures only logged-in users can call this
@csrf_protect   # CSRF protection
def setup_master_key_recovery(request):
  if request.method == 'POST':
    try:
      data = json.loads(request.body)
      phrase = data.get('phrase')
      master_key = data.get('master_key')

      if not phrase or not master_key:
        return JsonResponse({"status": "error", "message": "Missing data"}, status=400)

      # hashing the recovery phrase so we don't store it in plain text
      hashed_phrase = make_password(phrase.strip())

      # deriving a robust cryptographic key from the recovery phrase words
      crypto_key = derive_key(phrase.strip()) 
      f = Fernet(crypto_key)  # this starts the encryption process

      # encrypting the actual master_key using the recovery phrase's key
      # this locks the master key in a vault that only the recovery phrase can open
      encrypted_master_key_backup = f.encrypt(master_key.encode()).decode()

      # saving or update the record in the database for this specific user
      recovery_data, created = RecoveryKey.objects.update_or_create(
          user=request.user,
          defaults={
              'recovery_phrase_hash': hashed_phrase,
              'encrypted_master_key_backup': encrypted_master_key_backup
          }
      )
      print(f"Success! Backup secured for {request.user.username}")
      return JsonResponse({"status": "success", "message": "Backup secured!"})

    except json.JSONDecodeError:
      return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
      return JsonResponse({"status": "error", "message": f"Server error: {str(e)}"}, status=500)

  return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)



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
  password = master_key_string.encode() # converting the password into a byte representation

  salt = b'lab_project_salt_123'  # a 'salt' is random data added to the password before it's hashed
  kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),  # cryptographic hash 
    length=32,                  # Fernet requires a key that is exactly 32-bytes long
    salt=salt,
    iterations=100000,          # run the hash process 100000 times, to make the password as random as possible 
  )
  return base64.urlsafe_b64encode(kdf.derive(password))  # derive() produces those 100000 rounds of math and the 32-bytes 




def add_credential_view(request):
  if request.method == "POST":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])
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
        
    except PermissionDenied as error:
      return JsonResponse({"error": str(error)}, status=403)
    except json.JSONDecodeError:
      return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
  return JsonResponse({"error": "Only POST allowed"}, status=405)
         
         

def update_credential_view(request, cred_id):
  if request.method == "PUT":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])

      if not Credential.objects.filter(id=cred_id, user=token_user).exists():
        return JsonResponse({"error": "Unauthorized access to this resource"}, status=403)
      
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
        
    except PermissionDenied as error:
      return JsonResponse({"error": str(error)}, status=403)
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
  return JsonResponse({"error": "Only PUT allowed"}, status=405)



def delete_credential_view(request, cred_id):
  if request.method == "DELETE":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])
      success = service.delete_credential(cred_id)
      if success:
        return JsonResponse({"message": "Deleted successfully"}, status=200)
      else:
        return JsonResponse({"error": "Credential not found"}, status=404)
            
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
  return JsonResponse({"error": "Only DELETE allowed"}, status=405)



def add_note_view(request):
  if request.method == "POST":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])
      
      data = json.loads(request.body)
      serializer = SecuredNotesSerializer(data=data)
      
      if serializer.is_valid():
        new_note = serializer.save(user=token_user)
        return JsonResponse(SecuredNotesSerializer(new_note).data, status=201)
      else:
        return JsonResponse({"error": serializer.errors}, status=400)
            
    except PermissionDenied as error:
      return JsonResponse({"error": str(error)}, status=403)
    except json.JSONDecodeError:
      return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
  return JsonResponse({"error": "Only POST allowed"}, status=405)



def update_note_view(request, cred_id):
  if request.method == "PUT":
    try:
        token_user = check_token_scope(request, ["write_notes", "admin_access"])
        
        if not Note.objects.filter(id=cred_id, user=token_user).exists():
          return JsonResponse({"error": "Unauthorized access to this resource"}, status=403)
            
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
              
    except PermissionDenied as error:
      return JsonResponse({"error": str(error)}, status=403)
    except Exception as e:
      return JsonResponse({"error": str(e)}, status=500)
        
  return JsonResponse({"error": "Only PUT allowed"}, status=405)




def delete_note_view(request, note_id):
  if request.method == "DELETE":
    try:
      token_user = check_token_scope(request, ["write_notes", "admin_access"])
      
      if not Note.objects.filter(id=note_id, user=token_user).exists():
        return JsonResponse({"error": "Unauthorized access to this resource"}, status=403)
          
      success = service.delete_note(note_id)
      if success:
        return JsonResponse({"message": "Deleted successfully"}, status=200)
      else:
        return JsonResponse({"error": "Note not found"}, status=404)
            
    except PermissionDenied as error:
      return JsonResponse({"error": str(error)}, status=403)
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
          return Response(response_serializer.data, status=status.HTTP_201_CREATED)
      
        except Exception as e:
          return Response({"error": f"Encryption failed: {str(e)}"}, status=500)
        
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


method_decorator(csrf_exempt, name='dispatch')
class CredentialDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
      if not request.user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)
      print(f"DEBUG: Headers in view: {request.headers}")
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
    

    def put(self, request, pk):
      credential = get_object_or_404(Credential, pk=pk, user=request.user)
      master_key = request.headers.get('X-Master-Key')
      
      if not master_key:
        return Response({"error": "Master Key required"}, status=400)

      serializer = CredentialSerializer(credential, data=request.data)
      if serializer.is_valid():
          try:
              f = Fernet(get_crypto_key(master_key))
              plain_password = serializer.validated_data['password']
              encrypted_password = f.encrypt(plain_password.encode()).decode()
              
              # Save with the encrypted version
              serializer.save(password=encrypted_password)
              return Response(serializer.data)
          except Exception as e:
              return Response({"error": str(e)}, status=500)
      return Response(serializer.errors, status=400)


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
    print(f"DEBUG: Headers in view: {request.headers}")
    note = service.get_note_by_id(pk)
    if note is None:
        return Response({"error": "Note not found"}, status=404)

    master_key = request.headers.get('X-Master-Key')
    if master_key and note.bodytext.startswith('gAAAAA'):
        try:
            f = Fernet(get_crypto_key(master_key))
            try:
                note.bodytext = f.decrypt(note.bodytext.encode()).decode()
            except Exception:
                pass
        except Exception:
            return Response({"error": "Decryption setup failed"}, status=401)

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


@role_required("full_perms")
def api_statistics(request):
  try:
    # Enforce and validate the token scope
    token_user = check_token_scope(request, "admin_access")
    
    cred_count = Credential.objects.count()
    note_count = Note.objects.count()
    
    return JsonResponse({
        "labels": ["Credentials", "Notes"],
        "values": [cred_count, note_count]
    }, status=200)
      
  except PermissionDenied as divide_error:
    return JsonResponse({"error": str(divide_error)}, status=403)
  


@role_required("full_perms")
def api_security_stats(request):
  try:
    # Enforce and validate the token scope
    token_user = check_token_scope(request, "admin_access")
    
    suspicious_count = UserLog.objects.filter(is_suspicious=True).count()
    safe_count = UserLog.objects.filter(is_suspicious=False).count()
    
    return JsonResponse({
        "labels": ["Safe Actions", "Suspicious Actions"],
        "values": [safe_count, suspicious_count],
        "colors": ["#a4c639", "#d9534f"]
    }, status=200)
      
  except PermissionDenied as divide_error:
    return JsonResponse({"error": str(divide_error)}, status=403)




@login_required
def observation_list(request):  # this functions displays the suspicious events
  if not request.user.is_superuser and not request.user.role.name == "Admin":
    return redirect('home')

  suspicious_logs = UserLog.objects.filter(is_suspicious=True).order_by('-timestamp')

  return render(request, 'manager/statistics.html', {
    'suspicious-logs': suspicious_logs
  })


class EnableMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # generating a random secret for the user if they don't have one
        if not user.mfa_secret:
          user.mfa_secret = pyotp.random_base32()
          user.save()

        # creating the TOTP object
        totp = pyotp.TOTP(user.mfa_secret)
        
        # creating the URL that Authenticator apps understand
        provisioning_url = totp.provisioning_uri(
          name=user.email, 
          issuer_name="PasswordManager"
        )

        # generating a QR code image to send to the frontend
        img = qrcode.make(provisioning_url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        return Response({
          "qr_code": qr_base64, # send the image as a string
          "secret": user.mfa_secret # show the text secret as a backup
        })

class VerifyMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get("code") # the 6-digit code from the user

        if not user.mfa_secret:
          return Response({"error": "MFA not initialized"}, status=400)

        # verifying the code
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(code):
          user.is_mfa_enabled = True # OFFICIALLY ENABLED
          user.save()
          
          # generate backup codes 
          import uuid
          user.backup_codes = [str(uuid.uuid4())[:8] for _ in range(5)]
          user.save()
          
          return Response({
            "message": "MFA Enabled successfully!",
            "backup_codes": user.backup_codes
          })
        
        else:
          return Response({"error": "Invalid code. Try again."}, status=400)
   



