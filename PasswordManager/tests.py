from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from . import service
from .models import Note, Credential, CustomUser
from .serializers import CredentialSerializer, SecuredNotesSerializer

class CredentialTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')
        self.client.force_login(self.user)
        self.master_key = "test-key-123"


    def test_get_all_and_pagination(self):
        Credential.objects.create(
            user=self.user,  
            website_name="Site 1", url="https://s1.com",
            username="user1", email="1@test.com", password="123"
        )
        Credential.objects.create(
            user=self.user,  
            website_name="Site 2", url="https://s2.com",
            username="user2", email="2@test.com", password="456"
        )

        url = reverse('credential-list')
        response = self.client.get(url, {'page': 1, 'page_size': 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # showing only one credential per page
        self.assertEqual(response.data['count'], 2) # having a total of 2 credentials


    def test_create_credential_success(self):
        url = reverse('credential-list')
        data = {
            "website_name": "Google",
            "url": "https://google.com",
            "username": "user1",
            "email": "user@gmail.com",
            "password": "password123"
        }
        response = self.client.post(url, data, format='json', HTTP_X_MASTER_KEY=self.master_key)        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cred = Credential.objects.get()
        self.assertNotEqual(cred.password, "password123")
        self.assertTrue(cred.password.startswith("gAAAAA"))


    def test_create_credential_fail_validation(self):
        url = reverse('credential-list')
        data = {"password": "123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Credential.objects.count(), 0)


    # def test_get_single_credential_success(self):
    #     
    #     cred = Credential.objects.create(
    #         user=self.user, 
    #         website_name="FindMe", 
    #         url="https://test.com",
    #         username="testuser", 
    #         email="test@test.com", 
    #         password="gAAAAABm_some_fake_string" 
    #     )
        
    #     url = reverse('credential-detail', kwargs={'pk': cred.id})
        
    #     
    #     from rest_framework.test import force_authenticate
    #     self.client.force_authenticate(user=self.user)
        
    #     
    #     response = self.client.get(url, HTTP_X_MASTER_KEY=self.master_key)
        
    #     
    #     
    #     # self.client.force_authenticate(user=None)
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['website_name'], "FindMe")
            

    def test_get_single_credential_failure(self):
        """Should return 404 even if logged in if the ID doesn't exist."""

        url = reverse('credential-detail', kwargs={'pk': 999})
        response = self.client.get(url, HTTP_X_MASTER_KEY=self.master_key)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_update_credential_success(self):
        """Should update and re-encrypt the password."""
        cred = Credential.objects.create(
            user=self.user, # must link to logged-in user
            website_name="FindMe", 
            url="https://test.com",
            username="testuser", 
            email="test@test.com", 
            password="old-encrypted-string" 
        )
        url = reverse('credential-detail', kwargs={'pk': cred.id})
        
        updated_data = {
            "website_name": "New Name",
            "url": "https://new.com",
            "username": "newuser",
            "email": "new@email.com",
            "password": "newpassword123" 
        }
        
        # must send the Master Key for the PUT method to perform encryption
        response = self.client.put(url, updated_data, format='json', HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cred.refresh_from_db()
        
        self.assertEqual(cred.website_name, "New Name")
        self.assertNotEqual(cred.password, "newpassword123")
        self.assertTrue(cred.password.startswith("gAAAAA"))


    def test_delete_credential_success(self):
        """Should delete the record belonging to the user."""
        cred = Credential.objects.create(
            user=self.user, # must link to logged-in user
            website_name="FindMe", 
            url="https://test.com",
            username="testuser", 
            email="test@test.com", 
            password="encrypted-pass"
        )
        url = reverse('credential-detail', kwargs={'pk': cred.id})
        response = self.client.delete(url, HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Credential.objects.count(), 0)


    def test_delete_credential_failure(self):
        """Should return 404 for non-existent ID."""
        url = reverse('credential-detail', kwargs={'pk': 999})
        response = self.client.delete(url, HTTP_X_MASTER_KEY=self.master_key)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NotesTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')
        self.master_key = "test-master-key-456"


    def test_get_all_notes_pagination(self):
        Note.objects.create(user=self.user, headline="Note 1", bodytext="Encrypted_1")
        Note.objects.create(user=self.user, headline="Note 2", bodytext="Encrypted_2")
        
        url = reverse('notes-list') 
        response = self.client.get(url, {'page': 1, 'page_size': 1}, HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)


    def test_create_note_success(self):
        url = reverse('notes-list')
        data = {"headline": "My Diary", "bodytext": "I love Django"}
        response = self.client.post(url, data, format='json', HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.count(), 1)
        
        saved_note = Note.objects.get()
        self.assertNotEqual(saved_note.bodytext, "I love Django")
        self.assertTrue(saved_note.bodytext.startswith("gAAAAA"))


    def test_create_note_failure(self):
        url = reverse('notes-list')
        response = self.client.post(url, {}, format='json', HTTP_X_MASTER_KEY=self.master_key) 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_get_single_note_success(self):
        note = Note.objects.create(user=self.user, headline="Read Me", bodytext="gAAAAA_encrypted_stuff")
        url = reverse('notes-detail', kwargs={'pk': note.id})
        
        response = self.client.get(url, HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_get_single_note_failure(self):
        url = reverse('notes-detail', kwargs={'pk': 999})
        response = self.client.get(url, HTTP_X_MASTER_KEY=self.master_key)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_note_success(self):
        note = Note.objects.create(user=self.user, headline="Old", bodytext="Old_Encrypted")
        url = reverse('notes-detail', kwargs={'pk': note.id})
        data = {"headline": "New", "bodytext": "New Secret Content"}
        
        response = self.client.put(url, data, format='json', HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.headline, "New")
        self.assertTrue(note.bodytext.startswith("gAAAAA"))


    def test_delete_note_success(self):
        note = Note.objects.create(user=self.user, headline="Bye", bodytext="Poof")
        url = reverse('notes-detail', kwargs={'pk': note.id})
        response = self.client.delete(url, HTTP_X_MASTER_KEY=self.master_key)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Note.objects.count(), 0)


    def test_delete_note_failure(self):
        url = reverse('notes-detail', kwargs={'pk': 999})
        response = self.client.delete(url, HTTP_X_MASTER_KEY=self.master_key)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_user_cannot_access_others_notes(self):
        other_user = CustomUser.objects.create_user(username='hacker', password='password')
        Note.objects.create(user=other_user, headline="Hacker Secret", bodytext="hidden")
        
        url = reverse('notes-list')
        response = self.client.get(url, HTTP_X_MASTER_KEY=self.master_key)
        
        self.assertEqual(response.data['count'], 0)