from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from . import service

class CredentialTests(APITestCase):
    def setUp(self):
        service.credentials_list = []
        service.id_credentials = 1


    def test_get_all_and_pagination(self):
        service.add_credential({
          "website_name": "Site 1", 
          "url": "https://s1.com",
          "username": "user1",
          "email": "1@test.com",
          "password": "123"
        })

        service.add_credential({
          "website_name": "Site 2", 
          "url": "https://s2.com",
          "username": "user2",
          "email": "2@test.com",
          "password": "456"
        })

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
        self.assertEqual(response.data['id'], 1) # checking if ID 1 was assigned to the first item


    def test_create_credential_fail_validation(self):
        url = reverse('credential-list')
        data = {"password": "123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_get_single_credential_success(self):
        service.add_credential({
            "website_name": "FindMe", 
            "url": "https://test.com",
            "username": "testuser",  
            "email": "test@test.com",
            "password": "123"
        })
        url = reverse('credential-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['website_name'], "FindMe")
      

    def test_get_single_credential_failure(self):
        url = reverse('credential-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_update_credential_success(self):
        service.add_credential({
            "website_name": "FindMe", 
            "url": "https://test.com",
            "username": "testuser",  
            "email": "test@test.com",
            "password": "123"
        })
        url = reverse('credential-detail', kwargs={'pk': 1})
        updated_data = {
            "website_name": "New Name",
            "url": "https://new.com",
            "username": "newuser",
            "email": "new@email.com",
            "password": "newpassword"
        }
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['website_name'], "New Name")


    def test_delete_credential_success(self):
        service.add_credential({
            "website_name": "FindMe", 
            "url": "https://test.com",
            "username": "testuser",  
            "email": "test@test.com",
            "password": "123"
        })
        url = reverse('credential-detail', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(service.get_all_credentials()), 0)


    def test_delete_credential_failure(self):
        url = reverse('credential-detail', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NotesTests(APITestCase):
    def setUp(self):
        """Reset the in-memory lists before every test."""
        service.notes_list = []
        service.id_notes = 1


    def test_get_all_notes_pagination(self):
        service.add_note({"headline": "Note 1", "bodytext": "Secret 1"})
        service.add_note({"headline": "Note 2", "bodytext": "Secret 2"})
        
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
        self.assertEqual(response.data['id'], 1)
        self.assertEqual(response.data['headline'], "My Diary")


    def test_create_note_failure(self):
        url = reverse('notes-list')
        data = {"headline": ""} 
        response = self.client.post(url, {}, format='json') 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_single_note_success(self):
        service.add_note({"headline": "Read Me", "bodytext": "Top Secret"})
        url = reverse('notes-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bodytext'], "Top Secret")

    def test_get_single_note_failure(self):
        url = reverse('notes-detail', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_note_success(self):
        service.add_note({"headline": "Old", "bodytext": "Old News"})
        url = reverse('notes-detail', kwargs={'pk': 1})
        data = {"headline": "New", "bodytext": "New News"}
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['headline'], "New")

    def test_delete_note_success(self):
        service.add_note({"headline": "Bye", "bodytext": "Poof"})
        url = reverse('notes-detail', kwargs={'pk': 1})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(service.get_all_notes()), 0)

    def test_delete_note_failure(self):
        url = reverse('notes-detail', kwargs={'pk': 99})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)