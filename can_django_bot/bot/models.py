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

    name = models.TextField(
        null=True,
        verbose_name='Полное имя пользователя', 
    )

    is_in_payment = models.BooleanField(
        null=False,
        default=False
    )


    def __str__(self):
        return f"#{self.external_id} {self.name}"

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

class Transaction(models.Model):
    payment_id = models.PositiveBigIntegerField(
        verbose_name='ID транзакции',
        unique=True,
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
        return f"#{self.payment_id} {self.amount} {self.date}"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
