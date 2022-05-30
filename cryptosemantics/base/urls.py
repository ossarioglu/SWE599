import imp
from django.urls import path
from . import views

# These are URL patterns that webpage URL is to visit, parameters of these URL and action (views) done when visiting this URL 
urlpatterns = [

    # URL for home page
    path('', views.home, name="home"),
    path('search/', views.search, name="search"),
    path('detail/<qurl>', views.detailedView, name ="showdetails"),

    # URLs for user interactions : login, logout, sign-up, listing profile info, or updating profile
    path('login/', views.signinPage, name="login"),
    path('logout/', views.signOut, name="logout"),
    path('signup/', views.signUpPage, name="signup"),
    path('profile/<str:userKey>/', views.userProfile, name ="user-profile"), 
    path('update-profile/<str:userKey>/', views.updateProfile, name ="update-profile"), 

    path('save/<qurl>/', views.saveRecord, name ="save"), 
    path('deleter/<qurl>/', views.deleteRecord, name ="delete"), 

]
