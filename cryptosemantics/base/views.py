import string
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login, logout

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

import requests
import json
from django.http import JsonResponse

from .models import Searchresult, Profile
from .forms import MyRegisterForm


def home(request):
    context = {'offers':'', 'tags':'', 'offer_count':'', 'key':'', 'count':'', 'resultsWP':''}
    return render(request, 'base/home.html', context)


def search(request):
    
    myresult =[]
    keynote = ''

    search = request.GET.get('q') if request.GET.get('q') != None else ''
    selection = request.GET.get("listselection", None)
    
    dateexpression2 = datetime.strftime(datetime.today(), '%Y-%m-%d')
    dateexpression1 = datetime.strftime(datetime.today() - timedelta(days=365000), '%Y-%m-%d')

    if selection != '':

        if selection == "searchtoday":
            dateexpression1 = datetime.strftime(datetime.today() - timedelta(days=1), '%Y-%m-%d')
        if selection == "searchweek":
            dateexpression1 = datetime.strftime(datetime.today() - timedelta(days=7), '%Y-%m-%d')
        if selection == "searchmonth":
            dateexpression1 = datetime.strftime(datetime.today() - timedelta(days=30), '%Y-%m-%d')
        if selection == "searchyear":
            dateexpression1 = datetime.strftime(datetime.today() - timedelta(days=365), '%Y-%m-%d')
        if selection == "searchall":
            dateexpression1 = datetime.strftime(datetime.today() - timedelta(days=365000), '%Y-%m-%d')

        sqlArticle = f"""
            SELECT ?item ?itemLabel ?when (YEAR(?when) as ?date) ?DOI
            WHERE
            {{
            ?item wdt:P31 wd:Q13442814.  #Scientific article  
            ?item rdfs:label ?itemLabel.
            {{ ?item wdt:P921 wd:Q13479982 }} #Cryptocurrency
            UNION
            {{ ?item wdt:P921 wd:Q20514253 }} #Blockchain
            UNION
            {{ ?item wdt:P921 wd:Q109657450 }} #Blockchain Framework
            UNION
            {{ ?item wdt:P921 wd:Q10836209 }} #Digital Currency
            
            ?item wdt:P577 ?when.
            ?item wdt:P356 ?DOI.

            FILTER(CONTAINS(LCASE(?itemLabel), "{search}")).
            FILTER(CONTAINS(LANG(?itemLabel), "en")).
            
            FILTER ((?when > "{dateexpression1}"^^xsd:dateTime) && (?when <= "{dateexpression2}"^^xsd:dateTime)).
            }}
            ORDER BY DESC(?when)
        """
    
        sql = sqlArticle
        
        myresult = findArticlesWikidata(sql)
        mySaved = []
        if request.user.is_authenticated:
            userRecords = Searchresult.objects.filter(user=request.user)
            for list in userRecords:
                mySaved.append(list.searchCode)
        keynote = f'{len(myresult)} items are found having "{search}" at title'

    context = {'offers':'', 'tags':'', 'userRecords':mySaved, 'key':keynote, 'count':len(myresult), 'resultsWP':myresult}
  
    return render(request, 'base/search.html', context)

def detailedView(request, qurl):

  #  qurl.replace('http://www.wikidata.org/entity/', '')
    output = wikiAPI(qurl)

    for mylist in output['search']:
        mytitle = mylist['label']

    annotationlist= []
    annotationlist = showannotation(mytitle)

    context = {'alternative':annotationlist, 'mytitle': mytitle}
  #  context = {'results':output,'alternative':alternative}

    return render(request, 'base/detail.html', context) 

def findArticlesWikidata(wikisql):
    headers = {'User-Agent': 'CoolBot/0.0 (https://github.com/ossarioglu/SWE599/; osman.sarioglu@boun.edu.tr)'}
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql",agent=headers)
    sparql.setQuery(wikisql)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    result = results["results"]["bindings"]

    output = []
    for item in result:
        sub = []
        myQ = item["item"]["value"]
        myQ = myQ.replace('http://www.wikidata.org/entity/', '')
        sub.append(myQ)
        sub.append(item["item"]["value"])
        sub.append(item["itemLabel"]["value"])
        sub.append(item["when"]["value"])
        sub.append(item["date"]["value"])
        sub.append(item["DOI"]["value"])
        output.append(sub)
    return output

def findArticlesDBpedia(keys):

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(f'''
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?comment
        WHERE {{ <http://dbpedia.org/resource/{keys}> rdfs:comment ?comment
        FILTER (LANG(?comment)='en')
        }}''')
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    result = results["results"]["bindings"]

    finaloutput = ''
    for output in result:
        finaloutput = output["comment"]["value"]

    return finaloutput

def showannotation(expression):
    output = []
    new_string = expression.translate(str.maketrans('', '', string.punctuation))
    myList = new_string.split()
    for item in myList:
        sub = []
        sub.append(item)
        sub.append(refineannotaion(item))
        #sub.append(findArticlesDBpedia(item.capitalize()))
        output.append(sub)
    return output

def refineannotaion(expression):
    output = wikiAPI(expression)

    result = ''
    for mylist in output['search']: 
        print(result)
        if mylist['label'].lower() == expression.lower():
            if "description" in mylist:
                if mylist['description'] != 'Wikimedia disambiguation page':
                    result = result + '<p>' + mylist['description'] + '<p>'

    return result

def wikiAPI(query: str) -> JsonResponse:
    BASE_URL = 'https://www.wikidata.org/w/api.php'
    SEARCH_QS = '?action=wbsearchentities&format=json&language=en&type=item&continue=0&search={0}'

    request_uri = BASE_URL + SEARCH_QS.format(query)
    payload={}
    headers={'User-Agent': 'CoolBot/0.0 (https://github.com/ossarioglu/SWE599/; osman.sarioglu@boun.edu.tr)'}
    
    response = requests.request('GET', request_uri, headers=headers, data=payload).json()

    return response


# Sign-in Functionality
def signinPage(request):
    # Same frontend page is used for sign-in and sign-out. Page info is sent for Signin
    page = 'signin'
    
    # If user is already autheticated there is no need for sign-in, so page is redirected to home
    if request.user.is_authenticated:
        return redirect('home')
    
    # When info is entered at the sign-in page, username and password is validated
    # If they match, then user is autenticated, otherwise error message is rendered
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request,'User does not exist')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or password is not matching')
    
    # Page information is sent to frontend
    context = {'page':page}
    return render(request, 'base/signup_in.html', context)

# This is basic sign-out feature
def signOut(request):
    logout(request)
    return redirect('home')

# This is for sign-up of new users
def signUpPage(request):
    
    # Customized form for user information is called.
    form = MyRegisterForm()

    # When user details are posted, the information is matched with User model's field
    # Mandatory fields for quick signup is Username, Password, Name and Surname, Email, and Location 
    if request.method == 'POST':
        form = MyRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()
            login(request,user)
            
    # Django's default user model is used for User management. Therefore for further information about user is stored at Profile model
    # At quick signup, Location is a mandatory field from Profile model
    # New profile for this user is created and saved after adding Location information 
            newProfile = Profile.objects.create(user=user, userDetails=request.POST.get('userdetails'))
            newProfile.save()
    
    # After user is created, page is redirected to home page
    # Error is rendered in case there is problem in sign-up process 
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')
    
    return render(request, 'base/signup_in.html', {'form':form})

# This is for seeing user profile details
# Services offered by user is send to front-end
def userProfile(request, userKey):
    user = User.objects.get(username=userKey)
    context = {'user':user}
    return render(request, 'base/profile.html', context) 

# This is for updating user profile
# Login is required to see details of services 
@login_required(login_url='login')
def updateProfile(request, userKey):
    
    # Information from User and Profile is retrieved for authenticated user
    user = User.objects.get(username=userKey)
    myProfile = Profile.objects.get(user=user)

    # Authenticated user's information is called to Django's default UserCreation Form
    form = UserCreationForm(instance=user)

    if request.user != user:
        return HttpResponse('You are not allowed to update this profile')

    # When information is posted, it updates the user information for User and Profile models according to form's data
    # Returns back to home page after update is done.
    if request.method == 'POST':

        user.first_name = request.POST.get('firstName')
        user.last_name = request.POST.get('lastName')
        user.email = request.POST.get('email')
        user.save()

        myProfile.userLocation = request.POST.get('location')
        myProfile.userDetails = request.POST.get('userDetails')
        if request.FILES.get('picture') is not None:
            myProfile.userPicture = request.FILES.get('picture')
        myProfile.save()

        return redirect('home')
        
    context = {'form':form,'myProfile':myProfile, 'user':user}
    return render(request, 'base/update_profile.html', context)

def saveRecord(request, qurl):

  #  qurl.replace('http://www.wikidata.org/entity/', '')

    newSearch = Searchresult.objects.create(user=request.user, searchCode=qurl)
    newSearch.save()

    #context = {'alternative':annotationlist, 'mytitle': mytitle}

    return redirect('home')

def deleteRecord(request, qurl):
    offer = Searchresult.objects.get(user=request.user, searchCode=qurl)
    
    if request.user == request.user:
        offer.delete()
    
    return redirect('home')


def searchSaved(request):
    
    myresult =[]
    filtersql =''
    
    mySaved = []
    if request.user.is_authenticated:
        userRecords = Searchresult.objects.filter(user=request.user)
        for list in userRecords:
            mySaved.append(list.searchCode)
            filtersql = filtersql + '?item = wd:' + list.searchCode + '||'
            
    if len(mySaved) != 0:
        filtersql = filtersql[:-1]
        filtersql = filtersql[:-1]
        filtersql = 'FILTER(' + filtersql + ').'
        sqlArticle = f"""
            SELECT ?item ?itemLabel ?when (YEAR(?when) as ?date) ?DOI
            WHERE
            {{
            ?item wdt:P31 wd:Q13442814.  #Scientific article  
            ?item rdfs:label ?itemLabel.
            {{ ?item wdt:P921 wd:Q13479982 }} #Cryptocurrency
            UNION
            {{ ?item wdt:P921 wd:Q20514253 }} #Blockchain
            UNION
            {{ ?item wdt:P921 wd:Q109657450 }} #Blockchain Framework
            UNION
            {{ ?item wdt:P921 wd:Q10836209 }} #Digital Currency
            
            ?item wdt:P577 ?when.
            ?item wdt:P356 ?DOI.

            {filtersql}    

            FILTER(CONTAINS(LCASE(?itemLabel), "")).
            FILTER(CONTAINS(LANG(?itemLabel), "en")).            
            }}
            ORDER BY DESC(?when)
        """
        sql = sqlArticle
        
        print(sql)
        myresult = findArticlesWikidata(sql)
 
        context = {'offers':'', 'tags':'', 'userRecords':mySaved, 'key':'Saved Articles', 'count':len(myresult), 'resultsWP':myresult}
    
        return render(request, 'base/search.html', context)
    
    return HttpResponse('There are no recorded items')

