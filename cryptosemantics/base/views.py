from hashlib import new
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
        
        myresult = findArticlesWikidata(sql)
 
        context = {'offers':'', 'tags':'', 'userRecords':mySaved, 'key':'Saved Articles', 'count':len(myresult), 'resultsWP':myresult}
    
        return render(request, 'base/search.html', context)
    
    return HttpResponse('There are no recorded items')

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

def findArticlesWikidata(wikisql):
    #headers = 'User-Agent': 'SemanticSearchBot/0.0 (https://github.com/ossarioglu/SWE599/; osman.sarioglu@boun.edu.tr)'
    #headers = 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'
    headers = 'SemanticSearchBot/0.0 (https://github.com/ossarioglu/SWE599/; osman.sarioglu@boun.edu.tr)'
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

def detailedView(request, qurl):

    output = wikiAPI(qurl,'title')
    
    for mylist in output['search']:
        mytitle = mylist['label']

    annotationlist= []
    annotationlist, relationship = showannotation(mytitle)

    context = {'alternative':annotationlist, 'mytitle': mytitle, 'relationship':relationship}

    return render(request, 'base/detail.html', context) 

def showannotation(expression):
    output = []
    result = []
    newline= []
    new_string = expression.translate(str.maketrans('', '', string.punctuation))
    myList = new_string.split()

    newline.append('')
    newline.append(myList)
    result.append(newline)
    
    related =[]
    for item in myList:
        sub = []
        sub.append(item)
        sub.append(refineannotaion(item))
        related.append(getrelationshipfromWikidata(item))
        #sub.append(getrelationshipfromWikidata(item))
        output.append(sub)

    foundrelation = findsemantics(related)

    for i in range(len(foundrelation)):
        newline= []
        newline.append(myList[i])
        newline.append(foundrelation[i])
        result.append(newline)

    return output, result

def getrelationshipfromWikidata(expression):

# 'P31' : Instance of
# 'P279': Subclass
# 'P361': Part of
# 'P366': Has use
# 'P1343': Described by source
# 'P3095': Practiced by
# 'P1424': topic's of main template
# 'P1441': present in work
# 'P155': follows
# 'P156': followed by
# 'P910': topic's main category
# 'P4969': derivatice work
# 'P2283': uses
# 'P527': has part or parts
# 'P277': programming language
# 'P112': founded by
# 'P9059': subdivision of this unit

    output = wikiAPI(expression.lower(),'title')
    relatedresults = []
    result = []
    for mylist in output['search']: 
        if mylist['label'].lower() == expression.lower():
            if "description" in mylist:
                if mylist['description'] != 'Wikimedia disambiguation page':
                    result.append(mylist['id'])

    
    searchbyID = wikiAPI('|'.join(result),'id')
    
    relationship = []
    sublevel = []
    upperlevel =[]
    alllisted =[]

    if 'entities' in searchbyID:
        for entity_id in searchbyID['entities']:
            sublevel = []
            sublevel.append(entity_id)
            relationship = []
            for claim_id in searchbyID['entities'][entity_id]['claims']:
                if claim_id in ['P31', 'P279', 'P361', 'P366', 'P1343', 'P3095', 'P1424', 'P1441', 'P155', 'P156', 'P910', 'P4969', 'P2283', 'P527', 'P277', 'P112', 'P9059'  ]:
                    for claim in searchbyID['entities'][entity_id]['claims'][claim_id]:
                        relationship.append(claim['mainsnak']['datavalue']['value']['id'])
                        alllisted.append(claim['mainsnak']['datavalue']['value']['id'])
            sublevel.append(relationship)
            upperlevel.append(sublevel)

    relatedresults.append(result)
    relatedresults.append(alllisted)
    relatedresults.append(upperlevel)

    return relatedresults


def findsemantics(relatedlist):
    
    result = []
    relationship = [ [0] * len(relatedlist) for i in range(len(relatedlist)) ]

    for i in range(len(relatedlist)):
        j = 0
        while j < len(relatedlist):
            if i == j:
                j = j + 1
            if j < len(relatedlist):
                for item in relatedlist[i][0]:
                    subrelations = []
                    if item in relatedlist[j][1]:
                        subrelations.append(i)
                        subrelations.append(item)
                        subrelations.append(j)
                        result.append(subrelations)
                
                for item in relatedlist[i][1]:
                    subrelations = []
                    if item in relatedlist[j][1]:
                        subrelations.append(i)
                        subrelations.append(item)
                        subrelations.append(j)
                        result.append(subrelations)
            j = j + 1 
    
    for record in result:
        i = record[0];
        j = record[2];
        if i < j:
            relationship[i][j] += round(100/len(result),0)
        else:
            relationship[j][i] += round(100/len(result),0)
    
    return relationship

def refineannotaion(expression):
    output = wikiAPI(expression,'title')

    result = ''
    for mylist in output['search']: 
        if mylist['label'].lower() == expression.lower():
            if "description" in mylist:
                if mylist['description'] != 'Wikimedia disambiguation page':
                    result = result + '<p>' + mylist['description'] + '<p>'

    return result

def wikiAPI(query: str, selection:str) -> JsonResponse:
    BASE_URL = 'https://www.wikidata.org/w/api.php'
    
    if selection == 'title':
        SEARCH = '?action=wbsearchentities&format=json&language=en&type=item&continue=0&limit=50&search={0}'
    if selection == 'id':
        SEARCH = '?action=wbgetentities&ids={0}&languages=en&format=json'

    request_uri = BASE_URL + SEARCH.format(query)
    payload={}
    headers = {'User-Agent': 'SemanticSearchBot/0.0 (https://github.com/ossarioglu/SWE599/; osman.sarioglu@boun.edu.tr)'}
    
    response = requests.request('GET', request_uri, headers=headers, data=payload).json()

    return response

