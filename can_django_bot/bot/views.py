import json
import os

import requests
from django.http import JsonResponse
from django.views import View
from constants import *


TELEGRAM_URL = "https://api.telegram.org/bot"


# https://api.telegram.org/bot<token>/setWebhook?url=<url>/webhooks/tutorial/
class BotView(View):
    def post(self, request, *args, **kwargs):
        t_data = json.loads(request.body)
        t_message = t_data["message"]
        t_chat = t_message["chat"]

        try:
            text = t_message["text"].strip().lower()
        except Exception as e:
            return JsonResponse({"ok": "POST request processed"})

        text = text.lstrip("/")
        msg = 'Я распарсил твой запрос из джанги'

        self.send_message(f'А твое сообщение: <b>{text}</b>', t_chat["id"])
        self.send_message(msg, t_chat["id"])

        return JsonResponse({"ok": "POST request processed"})

    @staticmethod
    def send_message(message, chat_id):
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        response = requests.post(
            f"{TELEGRAM_URL}{TELEGRAM_BOT_TOKEN}/sendMessage", data=data
        )
