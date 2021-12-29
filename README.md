# CAN_bot
Чтобы запустить бота локально нужно:


1) Склонируем репозиторий
 bash```
	git clone <ссылка на репу> 	
```

2) Перейдем в папку
 bash```
        cd CAN_bot
```

3) Произведем миграции и мигрируем 
bash```
       	python manage.py makemigrations && python manage.py migrate
```

4) Можно создать суперюзера, но это необязательно 
bash```
       python manage.py createsuperuser
```

5) Запускаем веб-сервер
 bash```
       python manage.py runserver
```

6) Необходимо скачать ngrok и прокинуть порты, поскольку teleram api поддерживает только https запросы
 bash```
       ./ngrok http 8000
```

7) Устанавливаем вебхук, засунув такого вида ссылку в наш браузер
bash```
        https://api.telegram.org/bot<ваш токен>/setWebhook?url=<url которое дал ngrok>/webhooks/tutorial/
```

