from django.shortcuts import render


def home(request):
    

    context = {'offers':'', 'tags':'', 'offer_count':'','users':'', 'notes':'', 'offer_count_old':''}
    return render(request, 'base/home.html', context)
