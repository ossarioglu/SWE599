from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE
import uuid



# Create your models here.
class Profile(models.Model):
    
    # user has one-to-one relatiınship with User object
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    userDetails = models.TextField(max_length=200,null=True)
    userPicture = models.ImageField(upload_to='Profiles',null=True, default="male.png")
    def __str__(self):
        return f'{self.user.username}'

class Searchresult(models.Model):
    recordID = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    searchCode = models.CharField(max_length=15)
    def __str__(self):
        return self.tagName