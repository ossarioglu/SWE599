from django.test import TestCase
from base.models import Profile, Searchresult
from django.contrib.auth.models import User

# Unit tests for models at Base App
class TestAppModels(TestCase):

    @classmethod
    def setUpTestData(cls):
        #This is setup for objects to be used at tests
        cls.user = User.objects.create(username="myTestUser")
        cls.myProfile = Profile.objects.create(user=cls.user)
        cls.myResult = Searchresult.objects.create(user=cls.user, searchCode='Q12345')

    # These tests are to check whether object name will return expected result as model
    # This is for Profile model
    def test_model_Str1(self):
        self.assertEqual(str(self.myProfile),self.user.username)
    
       
    #This is for Offering model
    def test_model_Str3(self):
        myID = f'{self.myResult.recordID}'
        self.assertEqual(str(self.myResult),myID)

