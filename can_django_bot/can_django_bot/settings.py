"""
Django settings for can_django_bot project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from pathlib import Path

from nn_models.ru_sentiment_extraction import RUSentimentExtractor

from navec import Navec
import catboost


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-f8vgnwf&!dnhtu1ll*iy29p840eytcx3$z0fq@)h=8j@7lv+*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'bot.canb2b.ru', 'localhost', '37.18.121.207']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bot'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'can_django_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'can_django_bot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DB_NAME = 'bank'
DB_USER = 'canbot'
DB_PASSWORD = 'alina123#'
DB_HOST = '37.18.121.207'
DB_PORT = '5432'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATIC_URL = os.path.join(PROJECT_ROOT, 'static/')
STATICFILES_DIRS = ()


# Настройки бота
TELEGRAM_BOT_TOKEN = '5014183108:AAHoT3s1LHg6p485Cib719FMP_r0L5sf3x4'
PROVIDER_TOKEN = '390540012:LIVE:21580'

ONE_REVIEW_PRICE = 1500
CATEGORY_REVIEW_PRICE = 10000
NEW_USER_BONUS = 500
MIN_SUM_TO_ADD = 100

COMMANDS = {
    '/start' : 'Запуск бота',
    '/help': 'Узнать о возможностях бота',
    '/main': 'Перейти в главное меню', 
    '/wb': 'Анализ товаров на Wildberries',
    '/ozon': 'Анализ товаров на Ozon',
    '/balance':'Информация о балансе',
    '/balance_add':'Пополнить баланс',
    '/demo_report':'Посмотреть демо отчет',
    '/cancel':'Отменить текущую операцию'
}

COMMANDS_STRING = "\n".join([f"{item[0]} - {item[1]}" for item in COMMANDS.items()])

# Настройки моделей машинного обучения
embedding_model_path = './nn_models/navec_hudlit_v1_12B_500K_300d_100q.tar'
EMB_MODEL = Navec.load(embedding_model_path)

extractor_clf = catboost.CatBoostClassifier()
extractor_clf = extractor_clf.load_model('./nn_models/en_clf_model')

wrg_clf = catboost.CatBoostClassifier()
WRG_CLF = wrg_clf.load_model('./nn_models/wordnet_classifier_1')

EXTRACTOR = RUSentimentExtractor(vectorizer=EMB_MODEL, classifier=extractor_clf)

BANNED_ADJ_STEMMED = ['бесполезн', 'отличн', 'бомбов', 'бредов', 'важн', 'взрывн', 'возмутительн', 'гадк', 'гениальн', 'годн', 'друг', 'единствен', 'жалк', 'жив', 'забавн', 'идеальн', 'идентичн', 'изумительн', 'изящн', 'как', 'классн', 'крут', 'лев', 'люб', 'мил', 'модн', 'неверн', 'неплох', 'непохож', 'плох', 'хорош', 'прост', 'готов', 'серьезн', 'супер', 'классн', 'топ', 'бесподобн','очен', 'котор']
