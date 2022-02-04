from django.shortcuts import render, redirect
from django.conf import settings

from parsing.wb_crawler import parse_product


def index(request):
    if request.method == 'GET':
        return render(request, 'main.html')

    
        
