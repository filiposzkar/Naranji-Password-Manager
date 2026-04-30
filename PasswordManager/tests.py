from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from . import service
from .models import Note, Credential
from .serializers import CredentialSerializer, SecuredNotesSerializer

class CredentialTests(APITestCase):
    def setUp(self):
       pass


    def test_get_all_and_pagination(self):
        Credential.objects.create(
            website_name="Site 1", url="https://s1.com",
            username="user1", email="1@test.com", password="123"
        )
        Credential.objects.create(
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
        response = self.client.post(url, data, format='json') # self.client is like a fake browser
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Credential.objects.count(), 1)
        self.assertEqual(Credential.objects.get().website_name, "Google")


    def test_create_credential_fail_validation(self):
        url = reverse('credential-list')
        data = {"password": "123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Credential.objects.count(), 0)


    def test_get_single_credential_success(self):
        cred = Credential.objects.create(
            website_name="FindMe", url="https://test.com",
            username="testuser", email="test@test.com", password="123"
        )
        url = reverse('credential-detail', kwargs={'pk': cred.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['website_name'], "FindMe")
      

    def test_get_single_credential_failure(self):
        url = reverse('credential-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_update_credential_success(self):
        cred = Credential.objects.create(
            website_name="FindMe", url="https://test.com",
            username="testuser", email="test@test.com", password="123"
        )
        url = reverse('credential-detail', kwargs={'pk': cred.id})
        updated_data = {
            "website_name": "New Name",
            "url": "https://new.com",
            "username": "newuser",
            "email": "new@email.com",
            "password": "newpassword"
        }
        response = self.client.put(url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cred.refresh_from_db()
        self.assertEqual(cred.website_name, "New Name")


    def test_delete_credential_success(self):
        cred = Credential.objects.create(
            website_name="FindMe", url="https://test.com",
            username="testuser", email="test@test.com", password="123"
        )
        url = reverse('credential-detail', kwargs={'pk': cred.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Credential.objects.count(), 0)


    def test_delete_credential_failure(self):
        url = reverse('credential-detail', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NotesTests(APITestCase):
    def setUp(self):
        pass


    def test_get_all_notes_pagination(self):
        Note.objects.create(headline="Note 1", bodytext="Secret 1")
        Note.objects.create(headline="Note 2", bodytext="Secret 2")
        
        url = reverse('notes-list') 
        response = self.client.get(url, {'page': 1, 'page_size': 1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)


    def test_create_note_success(self):
        url = reverse('notes-list')
        data = {"headline": "My Diary", "bodytext": "I love Django"}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.get().headline, "My Diary")


    def test_create_note_failure(self):
        url = reverse('notes-list')
        response = self.client.post(url, {}, format='json') 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Note.objects.count(), 0)


    def test_get_single_note_success(self):
        note = Note.objects.create(headline="Read Me", bodytext="Top Secret")
        url = reverse('notes-detail', kwargs={'pk': note.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bodytext'], "Top Secret")


    def test_get_single_note_failure(self):
        url = reverse('notes-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_update_note_success(self):
        note = Note.objects.create(headline="Old", bodytext="Old News")
        url = reverse('notes-detail', kwargs={'pk': note.id})
        data = {"headline": "New", "bodytext": "New News"}
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.headline, "New")


    def test_delete_note_success(self):
        note = Note.objects.create(headline="Bye", bodytext="Poof")
        url = reverse('notes-detail', kwargs={'pk': note.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Note.objects.count(), 0)


    def test_delete_note_failure(self):
        url = reverse('notes-detail', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)