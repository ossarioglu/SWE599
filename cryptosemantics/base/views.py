from django.shortcuts import render
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime, timedelta

import requests
from django.http import JsonResponse



def home(request):
    
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

        sqlCrypto = """
            SELECT ?item ?itemLabel

            WHERE { 
            
                {?item wdt:P31 wd:Q13479982 . }
                    UNION
                {?item wdt:P31 wd:Q20514253 . }
                    UNION
                {?item wdt:P31 wd:Q109657450 . }
                    UNION
                {?item wdt:P31 wd:Q10836209 . }

                SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
            }   
        """



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
            FILTER ((?when > "{dateexpression1}"^^xsd:dateTime) && (?when <= "{dateexpression2}"^^xsd:dateTime)).
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
            }}
            ORDER BY DESC(?item)
        """
    
        sql = sqlArticle
        


        #context = {'offers':'', 'tags':'', 'offer_count':'','users':'', 'notes':'', 'offer_count_old':'', 'resultsWP':findArticlesWikidata(sql),'resultsDB':findArticlesDBpedia('Bitcoin')}
        myresult = findArticlesWikidata(sql)
    
    alternative = []

    for result in myresult:
        sub = []
        sub.append(splitExpression(result["itemLabel"]["value"]))
        sub.append(result["when"]["value"])
        sub.append(result["date"]["value"])
        alternative.append (sub)

    context = {'offers':'', 'tags':'', 'offer_count':'','alternative':alternative, 'key':search, 'count':len(myresult), 'resultsWP':myresult}
    return render(request, 'base/home.html', context)


def findArticlesWikidata(wikisql):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(wikisql)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def findArticlesDBpedia(keys):

    print(keys) 

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
        print(finaloutput) 

    return finaloutput

def splitExpression(expression):
    output = []
    myList = expression.split()
    for item in myList:
        sub = []
        print(datetime.now())
        sub.append(item)
        sub.append(wikiAPI(item))
        print(sub)
        #sub.append(findArticlesDBpedia(item.capitalize()))
        output.append(sub)
    return output


def wikiAPI(query: str) -> JsonResponse:
    BASE_URL = 'https://www.wikidata.org/w/api.php'
    SEARCH_QS = '?action=wbsearchentities&format=json&language=en&type=item&continue=0&search={0}'
    SEARCH_QS2 = '?action=wbgetentities&sites=enwiki&titles={0}&props=descriptions&languages=en&format=json'

    request_uri = BASE_URL + SEARCH_QS.format(query)
    payload={}
    headers={}
    
    response = requests.request('GET', request_uri, headers=headers, data=payload).json

  

    return response