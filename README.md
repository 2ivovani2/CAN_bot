# CAN_bot
Чтобы запустить бота локально нужно:


1) Склонируем репозиторий
```bash
git clone <ссылка на репу> 	
```

2) Перейдем в папку
```bash
cd CAN_bot
```

3) Необходимо в файл `settings.py` добавить наш токен в таком формате:<br>
```python
TELEGRAM_BOT_TOKEN = '<ваш токен>'
```

4) Произведем миграции и мигрируем 
```bash
python manage.py makemigrations && python manage.py migrate
```

5) Можно создать суперюзера, но это необязательно 
```bash
python manage.py createsuperuser
```

6) Запускаем веб-сервер
```bash
python manage.py runserver
```


![Поздравлямба](https://media.giphy.com/media/2WDKW6TCEqnJe/giphy.gif)

