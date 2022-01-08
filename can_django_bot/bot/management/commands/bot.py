from typing import Pattern
from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode, LabeledPrice
from telegram.ext import CallbackContext, Filters, MessageHandler, Updater, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler
from telegram.utils.request import Request

from uuid import uuid4

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
    """
        Функция обработчик, возвращающая django instance пользователя
    """

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message


    fullname = ''
    if message.chat.first_name:
        fullname += message.chat.first_name
    if message.chat.last_name:
        fullname += ' ' + message.chat.last_name

    instance, created = TGUser.objects.update_or_create(
        external_id = message.chat.id,
        username = message.chat.username,
        name = fullname
    )

    return instance

@log_errors
def start_command_handler(update:Update, context:CallbackContext):
    """
        Функция обработки команды /start
    """

    user = user_get_by_update(update)
    start_reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('О сервисе ⚡️', callback_data='keyboard_help')
        ],
        [
            InlineKeyboardButton('Отчет WB 📊', callback_data='wb_report'),
            InlineKeyboardButton('Отчет OZON 📊', callback_data='ozon_report')
        ],
        [
            InlineKeyboardButton('Баланс 💎', callback_data='balance_info'),
            InlineKeyboardButton('Пополнить 💰', callback_data='add_balance')
        ],
        [
            InlineKeyboardButton('Посмотреть демо отчет 🗂', callback_data='demo_report')
        ],
        
    ])

    context.bot.send_message(
        chat_id=user.external_id,
        text=f'Приветствую в главном меню, <b>{user.name}</b>!\n\nЗадача бота – помочь вам разобраться в своих товарах и отзывах на них. Выберите, что вас интересует ниже:',
        reply_markup=start_reply_markup,
        parse_mode = ParseMode.HTML
    )


@log_errors
def help_command_handler(update:Update, context:CallbackContext):
    """
        Функция обработки команды /help
    """
    
    user = user_get_by_update(update)

    context.bot.send_message(
        chat_id=user.external_id,
        text=f'📊 <b>Основное</b>:\nЭтот телеграм бот поможет собрать данные отзывов на товары на маркетплейсах и проанализировать их. Вы будете знать о достоинствах и недостатках ваших товаров или товарах ваших конкуретов. Посмотрите демо-отчет и убедитесь в качестве работы бота самостоятельно 😮‍💨\n\n💻 <b>Доступные команды</b>:\n{settings.COMMANDS_STRING}\n\n💸 <b>Стоимость услуг:</b>\nСтоимость полного анализа одной карточки товара равна <i><b>1000₽</b></i>, но чем больше товаров вы будете анализировать, тем меньше будет стоимость.\n\n📯 <b>Другое</b>:\nЕсли вам необходимо проанализировать тексовые данные, не относящиеся к тематике маркетплейсов, то напишите @i_vovani или @fathutnik и мы проанализируем их конкретно под вас.',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('Вернуться назад 🔙', callback_data='keyboard_back'),
            ],
            [
                InlineKeyboardButton('Посмотреть демо отчет 🗂', callback_data='demo_report')
            ],
        ]),
        parse_mode = ParseMode.HTML
    )

@log_errors
def pre_checkout_handler(update:Update, context:CallbackContext):
    # chat_id = update.to_dict()['pre_checkout_query']['from']['id']
    # user = TGUser.objects.get(external_id=chat_id)

    query_id = update.to_dict()['pre_checkout_query']['id']
    
    success = context.bot.answer_pre_checkout_query(
        pre_checkout_query_id=query_id, 
        ok=True,
    )

    print(context.bot.get_updates())
    print(success)

@log_errors
def balance_add_command_handler(update:Update, context:CallbackContext):
    """
        Функция обработки пополнения баланса пользователя
    """
    user = user_get_by_update(update)

    
    context.bot.send_invoice(
        chat_id=user.external_id,
        title='Пополнение баланса',
        description='Пополнение баланса',
        payload='Какой-то пэйлоад, не ебу че это',
        provider_token='381764678:TEST:32365',
        currency='RUB',
        prices=[
            LabeledPrice(
                label='Руб',
                amount=100000
            )
        ]
    )
    

class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):
        #1 - правильное подключение
        request = Request(
            connect_timeout = 0.5,
            read_timeout = 1.0
        )

        bot = Bot(
            request = request,
            token = settings.TELEGRAM_BOT_TOKEN,
        )

        #2 - обработчики
        updater = Updater(
            bot = bot,
            use_context = True,
        )

        ## обработчик /start
        start_handler = CommandHandler('start', start_command_handler)
        updater.dispatcher.add_handler(start_handler)

        ## обработчик /help
        help_handler = CommandHandler('help', help_command_handler)
        help_message_handler = MessageHandler(Filters.text & Filters.regex('О сервисе ⚡️'), help_command_handler)
        help_callback_handler = CallbackQueryHandler(help_command_handler, pattern='keyboard_help')

        updater.dispatcher.add_handler(help_handler)
        updater.dispatcher.add_handler(help_message_handler)
        updater.dispatcher.add_handler(help_callback_handler)

        ## обработчики работы с балансом
        balance_add_callback_handler = CallbackQueryHandler(balance_add_command_handler, pattern='add_balance')
        updater.dispatcher.add_handler(balance_add_callback_handler)

        updater.dispatcher.add_handler(PreCheckoutQueryHandler(pre_checkout_handler, pass_chat_data=True))
        
        #3 - запустить бесконечную обработку входящих сообщений
        updater.start_polling()
        updater.idle()
