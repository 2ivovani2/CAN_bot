from django.shortcuts import render, redirect
from django.conf import settings

from parsing.wb_crawler import parse_product


def index(request):
    if request.method == 'GET':
        emb_model = settings.EMB_MODEL
        wordnet = settings.WRG
        sent_extractor = settings.EXTRACTOR

        return render(request, 'main.html', {'wordnet':wordnet, 'emb':True if bool(emb_model) else False, 'sent_extractor':sent_extractor,})

    if request.method == 'POST':
        link = request.POST.get('link', '')

        name, photo, data = parse_product(link)
        print(name, photo, data)
        return redirect('/')
        
