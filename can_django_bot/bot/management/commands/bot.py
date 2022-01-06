from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, Filters, MessageHandler, Updater
from telegram.utils.request import Request

from bot.models import TGUser

def log_errors(f):
    """
        Функция обработчик ошибок бота, выводящая все в консоль
        @f:function - функция, которую надо проверить
    """
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except Exception as e:
            error_message = f"Произошла ошибка {e}"
            print(error_message)
            raise e

    return inner

def user_get_by_update(update: Update):
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    fullname = ''
    if message.chat.first_name:
        fullname += message.chat.first_name
    if message.from_user.last_name:
        fullname += ' ' + message.chat.last_name

    instance, created = TGUser.objects.update_or_create(
        external_id = message.chat.id,
        username = message.chat.username,
        name = fullname
    )

    return instance

@log_errors
def do_echo(update:Update, context:CallbackContext):
    user = user_get_by_update(update)
    text = update.message.text

    reply_text = f"Ваш id = {user.external_id} \n\n {text}"
    context.bot.send_message(user.external_id, reply_text)


class Command(BaseCommand):
    help = 'Команда запуска телграм бота'

    def handle(self, *args, **kwargs):
        #1 - правильное подключение
        request = Request(
            connect_timeout = 1.0,
            read_timeout = 2.0
        )

        bot = Bot(
            request = request,
            token = settings.TELEGRAM_BOT_TOKEN,
            
        )

        print(bot.get_me())

        #2 - обработчики
        updater = Updater(
            bot = bot,
            use_context = True
        )

        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(message_handler)

        #3 - запустить бесконечную обработку входящих сообщений
        updater.start_polling()
        updater.idle()
