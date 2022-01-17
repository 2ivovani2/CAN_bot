from django.shortcuts import render
from django.conf import settings

def index(request):
    emb_model = settings.EMB_MODEL
    wordnet = settings.WRG
    sent_extractor = settings.EXTRACTOR

    return render(request, 'main.html', {'wordnet':wordnet, 'emb':emb_model, 'sent_extractor':sent_extractor})