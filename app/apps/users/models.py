from django.db import models
from django.contrib.auth.models import User
import random
import string

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь", null=True, blank=True)
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    phone_number = models.CharField("Номер телефона", max_length=20, unique=True)
    client_code = models.CharField("Код клиента", max_length=10, unique=True, editable=False)
    created_at = models.DateTimeField("Дата регистрации", auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.client_code:
            self.client_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            # Generate 3-4 digit code
            code = str(random.randint(100, 9999))
            if not ClientProfile.objects.filter(client_code=code).exists():
                return code

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client_code})"

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"
        ordering = ['-created_at']
