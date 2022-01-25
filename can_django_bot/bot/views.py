from django.shortcuts import render
from django.conf import settings
from parsing.wb_crawler import parse_product

def index(request):
    emb_model = settings.EMB_MODEL
    wordnet = settings.WRG
    sent_extractor = settings.EXTRACTOR

    return render(request, 'main.html', {'wordnet':wordnet, 'emb':True if bool(emb_model) else False, 'sent_extractor':sent_extractor,})