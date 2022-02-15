from django.shortcuts import render, redirect
from parsing.wb_crawler import parse_product
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def index(request):
    if request.method == 'GET':
        return render(request, 'main.html')

@csrf_exempt
def parse_wb_data(request):
    """
        Функция сбора данных с wb по одной карточке
    """

    if request.method == 'GET':
        return redirect('/')

    if request.method == 'POST':
        link = request.POST.get('link', None)

        if bool(link):
            try:
                title, image, data = parse_product(link)
    
                return JsonResponse({
                    'status':200,
                    'title':title,
                    'image':image,
                    'data':data.to_json(force_ascii=False)
                })
            except Exception as e:
                return JsonResponse({
                    'status':500,
                    'error':"Your link is incorrect",
                })
        else:
            return JsonResponse({
                'status':500,
                'error':"There is no link in request"
            })
