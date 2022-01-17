from email.mime import image
from typing import Pattern
from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, LabeledPrice
from telegram.ext import CallbackContext, Filters, MessageHandler, Updater, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, ConversationHandler
from telegram.utils.request import Request

from bot.models import *
from bot.report_generation import generate_report

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

    if fullname.strip() == '':
        fullname = message.chat.username

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
            InlineKeyboardButton('Пополнить счет 💰', callback_data='balance_add')
        ],
        [
            InlineKeyboardButton('Посмотреть демо отчет 🗂', callback_data='demo_report')
        ],
        
    ])

    context.bot.send_message(
        chat_id=user.external_id,
        text=f'✋🏼 Приветствую в главном меню, <b>{user.name}</b>!\n\nЗадача бота – помочь вам разобраться в своих товарах и отзывах на них. Выберите, что вас интересует ниже:',
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
        text=f'📊 <b>Основное</b>:\nЭтот телеграм бот поможет собрать данные отзывов на товары на маркетплейсах и проанализировать их. Вы будете знать о достоинствах и недостатках ваших товаров или товарах ваших конкуретов. Посмотрите демо-отчет и убедитесь в качестве работы бота самостоятельно 😮‍💨\n\n💻 <b>Доступные команды</b>:\n{settings.COMMANDS_STRING}\n\n💸 <b>Стоимость услуг:</b>\nСтоимость полного анализа одной карточки товара равна <i><b>1000₽</b></i>, но чем больше товаров вы будете анализировать, тем меньше будет стоимость.\n\n👁 <b>Принцип работы</b>:\nВы пополняете баланс -> Выбираете необходимую услугу -> Бот собирает данные, анализирует -> Конечный отчет в формате PDF\n\n📯 <b>Другое</b>:\nЕсли вам необходимо проанализировать тексовые данные, не относящиеся к тематике маркетплейсов, то напишите @i_vovani или @fathutnik и мы проанализируем их конкретно под вас.',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('Посмотреть демо отчет 🗂', callback_data='demo_report')
            ],
            [
                InlineKeyboardButton('Отчет WB 📊', callback_data='wb_report'),
                InlineKeyboardButton('Отчет OZON 📊', callback_data='ozon_report')
            ],

        ]),
        parse_mode = ParseMode.HTML
    )

@log_errors
def pre_checkout_handler(update:Update, context:CallbackContext):
    """
        Функция конечного потдверждения операции оплаты
    """

    chat_id = update.to_dict()['pre_checkout_query']['from']['id']
    user = TGUser.objects.get(external_id=chat_id)

    query_id = update.to_dict()['pre_checkout_query']['id']

    total_amount = int(str(update.to_dict()['pre_checkout_query']['total_amount'])[:-2])

    success = context.bot.answer_pre_checkout_query(
        pre_checkout_query_id=query_id, 
        ok=True,
    )

    if success:
        user.is_in_payment = False
        user.balance += total_amount
        user.save()

        transaction = Transaction(
            payment_id=query_id,
            amount=int(total_amount),
            user=user 
        )

        transaction.save()

        context.bot.send_message(
            chat_id=user.external_id,
            text='🤑 Ваш счет пополнен. Можете пользоваться услугами бота.'
        )
    
    else:
        context.bot.send_message(
            chat_id=user.external_id,
            text='😱 Произошла какая-то техническая ошибка. Попробуйте повторить запрос позже. \n\n* Если по каким-то причинам у вас списались средства, но баланс не обновился, то напишите @i_vovani или @fathutnik и мы вам обязательно поможем.😉'
        )
    
@log_errors
def text_handler(update:Update, context:CallbackContext):
    """
        Функция обработки различного текста от пользователя
    """

    user = user_get_by_update(update)

    if user.is_in_payment:
        user_message = update.message.text
        try:
            amt = int(user_message)
            if amt >= 1000:
                context.bot.send_message(
                    chat_id=user.external_id,
                    text=f'Отлично, высылаю форму для пополнения баланса на сумму <i><b>{amt}₽</b></i>.',
                    parse_mode=ParseMode.HTML
                ) 
                
                context.bot.send_invoice(
                    chat_id=user.external_id,
                    title='CAN Sentiment Analysis',
                    description=f'Пополнение баланса пользователя {user.username} на сумму {amt}₽',
                    payload=f'Пополнение баланса пользователя {user.username} на сумму {amt}₽',
                    provider_token='381764678:TEST:32365',
                    currency='RUB',
                    prices=[
                        LabeledPrice(
                            label='Пополнение',
                            amount=int(f'{amt}00')
                        )
                    ]
                )

            else:
                user.is_in_payment = False
                user.save()
                context.bot.send_message(
                    chat_id=user.external_id,
                    text='😵‍💫 К сожалению, мы не можем обработать ваш запрос, поскольку минимальная сумма платежа - <i><b>1000₽</b></i>.',
                    parse_mode=ParseMode.HTML
                ) 
        except:
            user.is_in_payment = False
            user.save()
            context.bot.send_message(
                chat_id=user.external_id,
                text='😵‍💫 К сожалению, мы не можем обработать ваш запрос, так как вы ввели некорректное значение, либо сумма слишком большая.\n\n<b>Пример:</b>\n1000 или 3657 или 1001. Обычное целое число.',
                parse_mode=ParseMode.HTML
            )

    else:
        context.bot.send_message(
                chat_id=user.external_id,
                text='😵 Мои создатель пока не научили меня отвечать на такие сообщения. ',
                parse_mode=ParseMode.HTML
            )

@log_errors
def balance_add_command_handler(update:Update, context:CallbackContext):
    """
        Функция обработки пополнения баланса пользователя
    """
    user = user_get_by_update(update)
    user.is_in_payment = True
    user.save()
    
    context.bot.send_message(
        chat_id=user.external_id,
        text='🤑 Введите сумму пополения:\n\n*миниамальная сумма пополнения - <i><b>1000₽</b></i>',
        parse_mode=ParseMode.HTML
    )
    
@log_errors
def balance_info(update:Update, context:CallbackContext):
    """
        Функция, сообщающая пользователю его баланс
    """
    user = user_get_by_update(update)

    context.bot.send_message(
        chat_id=user.external_id,
        text=f'Уважаемый {user.name}, на сегодняшний день баланс вашего счета составляет <i><b>{user.balance}₽</b></i>',
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('В главное меню 👈🏼', callback_data='keyboard_main'),
                InlineKeyboardButton('Пополнить счет 💰', callback_data='balance_add')
            ],

        ]),
    )

@log_errors
def demo_report_handler(update: Update, context: CallbackContext):
    """
       Функция, которая генерирует демо отчет
    """
    user = user_get_by_update(update)

    context.bot.send_message(
        chat_id=user.external_id,
        text='👁 Секундочку... Мы готовим демо отчет...'
    )

    demo_data = {
        "достоинства": {
            "Приятный запах": {
                "examples": [
                    "Экономно, хороший шампунь, приятный запах!",
                    "Хороший шампунь, приятный запах, волосы лёгкие и шелковистые."
                ],
                "rates": [
                    5,
                    5
                ],
                "mean_rate": 5.0
            },
            "Доставка быстрая": {
                "examples": [
                    "Доставка быстрая,всё упаковано хорошо,пользуюсь с удовольствием👍легкий не навязчивый аромат,бесцветный.",
                    "Отлично упакован,доставка быстрая,для моих кератиновых-отлично!",
                    "Доставка быстрая.",
                    "Шампунь очень хороший, доставка быстрая.",
                    "Доставка быстрая.",
                    "Доставка быстрая, беру первый раз, ещё не пользовалась, немного расстроила крышка которая не встаёт на место и имеется щель, при наклоне может вытечь содержимое.",
                    "Доставка быстрая",
                    "Доставка быстрая, флакон без деформации, НО.....около 100мл не хватает )",
                    "Доставка быстрая, пришло все в целости и сохранности !",
                    "Доставка быстрая, курьером) шампунь немного протек, но не страшно, но очень понравился в использовании запах нормальны с ним заказывала ещё бальзам!"
                ],
                "rates": [
                    5,
                    5,
                    5,
                    5,
                    5,
                    4,
                    5,
                    5,
                    5,
                    5
                ],
                "mean_rate": 4.9
            },
            "Упаковка целая": {
                "examples": [
                    "Пришел, буквально за пару дней, упаковка целая, я довольна",
                    "Упаковка целая, повреждений никаких не было.",
                    "Упаковка целая.",
                    "Прошёл быстро,упаковка целая.",
                    "Упаковка целая.",
                    "Упаковка целая , литра хватает на полгода .",
                    "Упаковка целая.",
                    "Товар хороший упаковка целая",
                    "Упаковка целая."
                ],
                "rates": [
                    5,
                    5,
                    5,
                    4,
                    5,
                    5,
                    5,
                    5,
                    5
                ],
                "mean_rate": 4.9
            },
            "Бутылка целая": {
                "examples": [
                    "Хороший шампунь , все запечатано , бутылка целая",
                    "Пришло упаковано в пакетик, бутылка целая.",
                    "Бутылка целая, не вскрытая."
                ],
                "rates": [
                    5,
                    5,
                    5
                ],
                "mean_rate": 5.0
            },
            "Доставка отличная": {
                "examples": [
                    "Доставка отличная.",
                    "Доставка отличная: пришло быстро и хорошо запакованным - в 3 слоя пленки.",
                    "Доставка отличная!"
                ],
                "rates": [
                    5,
                    5,
                    5
                ],
                "mean_rate": 5.0
            },
        },
        "недостатки": {
            "Коробка мокрая": {
                "examples": [
                    "пришёл шампунь, упакован хорошо, но вытек шампунь, вся коробка мокрая."
                ],
                "rates": [
                    3
                ],
                "mean_rate": 3.0
            },
            "Упаковка обычная": {
                "examples": [
                    "Очень расстроена, в пункте выдачи не обратила внимание, но когда пришла домой и стала снимать упаковку (обычная пупырка) - обнаружила,что крышка была открыта и очень много шампуня вылилось."
                ],
                "rates": [
                    1
                ],
                "mean_rate": 1.0
            },
            "Этикеткой длинный": {
                "examples": [
                    "К шампуню нет никаких претензий, но под этикеткой длинный волос!"
                ],
                "rates": [
                    1
                ],
                "mean_rate": 1.0
            },
            "Запах дешевый": {
                "examples": [
                    "Запах у шампуня дешевый цветочный."
                ],
                "rates": [
                    1
                ],
                "mean_rate": 1.0
            }
        }
    }

    image_link = 'https://images.wbstatic.net/c246x328/new/7540000/7546161-1.jpg'
    product_name = 'ESTEL PROFESSIONAL / Шампунь для волос'

    pdf = generate_report(demo_data, image_link, product_name)

    context.bot.send_document(
        chat_id=user.external_id,
        document=pdf,
        caption=f'<b>{user.name}</b>, вот так выглядят отчеты.',
        filename='demo_report.pdf',
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('В главное меню 👈🏼', callback_data='keyboard_main'),
            ],

        ]),
    )

@log_errors
def ozon_report_handler(update: Update, context: CallbackContext):
    """
        Функция обработки ozon
    """

    user = user_get_by_update(update)

    context.bot.send_message(
        chat_id=user.external_id,
        text='👀 <b>Мы становимся лучше для вас!</b>\nСбор данных с Ozon пока находится в разработке, но если у вас есть свои данные, то напишите @i_vovani или @fathutnik и мы сделаем отчет специально под вас за ту же стоимость.',
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('В главное меню 👈🏼', callback_data='keyboard_main'),
            ],
            [
                InlineKeyboardButton('Написать 🗣', url='https://t.me/i_vovani'),
            ],

        ]),
    )

class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):
        #1 - правильное подключение
        request = Request(
            connect_timeout = 1.0,
            read_timeout = 1.5
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

        menu_handler = CommandHandler('main', start_command_handler)
        updater.dispatcher.add_handler(menu_handler)

        menu_callback_handler = CallbackQueryHandler(start_command_handler, pattern='keyboard_main')
        updater.dispatcher.add_handler(menu_callback_handler)

        ## обработчик /help
        help_handler = CommandHandler('help', help_command_handler)
        updater.dispatcher.add_handler(help_handler)

        help_callback_handler = CallbackQueryHandler(help_command_handler, pattern='keyboard_help')
        updater.dispatcher.add_handler(help_callback_handler)

        ## обработчик ozon
        updater.dispatcher.add_handler(CommandHandler('ozon', ozon_report_handler))    
        updater.dispatcher.add_handler(CallbackQueryHandler(ozon_report_handler, pattern='ozon_report'))

        ## обработчик  демо отчета
        updater.dispatcher.add_handler(CommandHandler('demo_report', demo_report_handler))
        updater.dispatcher.add_handler(CallbackQueryHandler(demo_report_handler, pattern='demo_report'))

        ## обработчики работы с балансом
        
        updater.dispatcher.add_handler(PreCheckoutQueryHandler(pre_checkout_handler, pass_chat_data=True))
        updater.dispatcher.add_handler(CallbackQueryHandler(balance_info, pattern='balance_info'))
        updater.dispatcher.add_handler(CallbackQueryHandler(balance_add_command_handler, pattern='balance_add'))
        
        updater.dispatcher.add_handler(CommandHandler('balance_add', balance_add_command_handler))    
        

        ## обработчик текста, после него нельзя добавлять обработчики
        updater.dispatcher.add_handler(MessageHandler(Filters.text, text_handler))

        #3 - запустить бесконечную обработку входящих сообщений
        updater.start_polling()
        updater.idle()
