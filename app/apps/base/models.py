from django.db import models


class SiteSettings(models.Model):
    site_name = models.CharField("Название сайта", max_length=100, default="KG Cargo")
    organization = models.CharField("Организация", max_length=200, default="KG Cargo")
    address = models.CharField("Адрес", max_length=300, default="г. Бишкек")
    phone = models.CharField("Телефон", max_length=30, default="+996 XXX XXX XXX")

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
