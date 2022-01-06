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

    def __str__(self):
        return f"#{self.external_id} {self.name}"

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'