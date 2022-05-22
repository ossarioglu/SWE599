import string
from django.shortcuts import render
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime, timedelta

import requests
import json
from django.http import JsonResponse



def home(request):
    context = {'offers':'', 'tags':'', 'offer_count':'', 'key':'', 'count':'', 'resultsWP':''}
    return render(request, 'base/home.html', context)


def search(request):
    
    myresult =[]

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
        
        print(sql)
        myresult = findArticlesWikidata(sql)

    context = {'offers':'', 'tags':'', 'offer_count':'', 'key':search, 'count':len(myresult), 'resultsWP':myresult}
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
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
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
    headers={}
    
    response = requests.request('GET', request_uri, headers=headers, data=payload).json()

    return response