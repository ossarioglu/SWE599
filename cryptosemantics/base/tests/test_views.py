from django.http import response
from django.test import TestCase, Client, client
from base.views import *
from django.urls import reverse
from base.models import *
import json
from django.contrib.auth import authenticate,login, logout 
from django.contrib.auth.models import User

class TestAppViews(TestCase):

    @classmethod
    def setUpTestData(cls):
        
        #This is setup for objects to be used at tests
        cls.user = User.objects.create(username="myTestUser", password="MySecretPass")
        cls.myProfile = Profile.objects.create(user=cls.user)
        cls.myResult = Searchresult.objects.create(user=cls.user, searchCode='Q12345')

        cls.client = Client()
        cls.home_url = reverse('home')
        cls.signInPage_url = reverse('login')
        cls.signup_url = reverse('signup')
        cls.signout_url = reverse('logout')
        cls.search_url = reverse('search')
        cls.searchsaved_url = reverse('searchsaved')
        cls.showdetails_url = reverse('showdetails', kwargs={'qurl': str(cls.myResult.searchCode)})
        cls.userProfile_url = reverse('user-profile', kwargs={'userKey': cls.user.username})
        cls.showdetails_url = reverse('save', kwargs={'qurl': str(cls.myResult.searchCode)})
        cls.showdetails_url = reverse('delete', kwargs={'qurl': str(cls.myResult.searchCode)})

    #Testing for checking home url is working
    def test_view_home_GET(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'base/home.html')
    
    #Testing for checking sign in url is working
    def test_view_signInPage_GET(self):
        response = self.client.get(self.signInPage_url)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'base/signup_in.html')
   
    #Testing for checking sign up url is working
    def test_view_signupPage_GET(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'base/signup_in.html')

    #Testing for checking logout url is working
    def test_view_logout_GET(self):
        response = self.client.get(self.signout_url)
        self.assertEqual(response.status_code,302)  

    #Testing for checking userProfile url is working
    def test_view_userProfile_GET(self):
        response = self.client.get(self.userProfile_url)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'base/profile.html')
  
