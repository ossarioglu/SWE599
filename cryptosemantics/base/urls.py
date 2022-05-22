import imp
from django.urls import path
from . import views

# These are URL patterns that webpage URL is to visit, parameters of these URL and action (views) done when visiting this URL 
urlpatterns = [

    # URL for home page
    path('', views.home, name="home"),
    path('search/', views.search, name="search"),
    path('detail/<qurl>', views.detailedView, name ="showdetails"),
]