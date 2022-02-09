from django.db import models

class TGUser(models.Model):
    username = models.CharField(
        max_length=255,
        null=True,
        verbose_name='Имя пользователя'
    )
    
    external_id = models.PositiveBigIntegerField(
        verbose_name='ID телеграмм',
        unique=True
    )
    
    balance = models.FloatField(
        null=False,
        default=0.00,
        verbose_name='Баланс пользователя'
    )

    name = models.CharField(
        null=True,
        max_length=255,
        verbose_name='Полное имя пользователя', 
    )


    def __str__(self):
        return f"#{self.external_id} {self.name}"

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

class Transaction(models.Model):
    telegram_payment_charge_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='ID транзакции с системе Telegram', 
        null=True
    )

    provider_payment_charge_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='ID транзакции с системе ЮКасса', 
        null=True
    )

    invoice_payload = models.TextField(
        verbose_name='Описание платежа', 
        null=True
    )

    amount = models.FloatField(
        verbose_name='Сумма пополнения',
        null=False,
        default=0.0
    )

    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время'
    )

    user = models.ForeignKey(
        TGUser,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"#{self.user} {self.amount} {self.date}"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
