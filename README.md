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

4) Теперь на машину необходимо накатить некоторые плагины:<br>
### MacOS
```bash
brew install wkhtmltopdf
```
### Ubuntu
```bash
sudo apt-get install wkhtmltopdf
```

5) Установить nltk 
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

6) Произведем миграции и мигрируем 
```bash
python manage.py makemigrations && python manage.py migrate
```

7) Можно создать суперюзера, но это необязательно 
```bash
python manage.py createsuperuser
```

8) Запускаем веб-сервер для работы с админкой
```bash
python manage.py runserver
```

9) Запускаем бота
```bash
python manage.py bot
```

![Поздравлямба](https://media.giphy.com/media/2WDKW6TCEqnJe/giphy.gif)

