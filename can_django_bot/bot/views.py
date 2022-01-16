from django.shortcuts import render



def index(request):
    

    return render(request, '<h1>Всем привет, я Олег</h1>')