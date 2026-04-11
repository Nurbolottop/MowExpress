import random
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.users.models import ClientProfile

class ShipmentStatus(models.TextChoices):
    SENT = 'sent', _('Отправлено')
    IN_TRANSIT = 'in_transit', _('В пути')
    RECEIVED = 'received', _('Получено (в РФ)')
    ISSUED = 'issued', _('Выдано клиенту')


class ShipmentCategory(models.TextChoices):
    CLOTHES = 'clothes', _('Одежда')
    SHOES = 'shoes', _('Обувь')
    ELECTRONICS = 'electronics', _('Электроника')
    HOUSEHOLD = 'household', _('Бытовая техника')
    COSMETICS = 'cosmetics', _('Косметика')
    FOOD = 'food', _('Продукты питания')
    DOCUMENTS = 'documents', _('Документы')
    MEDICINE = 'medicine', _('Медикаменты')
    TOYS = 'toys', _('Игрушки')
    BOOKS = 'books', _('Книги')
    FURNITURE = 'furniture', _('Мебель')
    AUTO_PARTS = 'auto_parts', _('Автозапчасти')
    BUILDING = 'building', _('Стройматериалы')
    TEXTILES = 'textiles', _('Текстиль')
    ACCESSORIES = 'accessories', _('Аксессуары')
    SPORTS = 'sports', _('Спорттовары')
    FRAGILE = 'fragile', _('Хрупкое')
    OVERSIZED = 'oversized', _('Негабаритный')
    OTHER = 'other', _('Другое')


class Shipment(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='shipments', verbose_name="Клиент")
    waybill_number = models.CharField("Номер накладной", max_length=30, unique=True, blank=True)
    category = models.CharField("Категория", max_length=30, choices=ShipmentCategory.choices, default=ShipmentCategory.OTHER)
    weight = models.DecimalField("Вес (кг)", max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField("Стоимость за кг ($/сом)", max_digits=10, decimal_places=2)
    total_price = models.DecimalField("Итоговая сумма", max_digits=15, decimal_places=2, editable=False)
    delivery_address = models.CharField("Город назначения", max_length=255, blank=True, default="")
    status = models.CharField("Статус", max_length=20, choices=ShipmentStatus.choices, default=ShipmentStatus.SENT)
    shipping_date = models.DateField("Дата отправки", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    notes = models.TextField("Примечания", blank=True, null=True)

    @staticmethod
    def _generate_waybill_number():
        now = timezone.now()
        date_part = now.strftime('%y%m%d')
        time_part = now.strftime('%H%M%S')
        rand_part = str(random.randint(100, 999))
        return f"{date_part}{time_part}{rand_part}"

    def recalculate_totals(self, save=True):
        items = self.items.all()
        expenses = self.expenses.all()
        items_weight = sum(item.weight for item in items)
        items_total = sum(item.total_amount for item in items)
        expenses_total = sum(expense.total_amount for expense in expenses)
        self.weight = items_weight or 0
        self.total_price = (items_total or 0) + (expenses_total or 0)
        self.price_per_kg = (items_total / items_weight) if items_weight else 0
        if save:
            self.save(update_fields=['weight', 'total_price', 'price_per_kg'])

    def save(self, *args, **kwargs):
        if 'update_fields' not in kwargs:
            self.total_price = self.weight * self.price_per_kg
        if not self.waybill_number:
            for _ in range(10):
                num = self._generate_waybill_number()
                if not Shipment.objects.filter(waybill_number=num).exists():
                    self.waybill_number = num
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ {self.id} - {self.client.client_code} ({self.status})"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-shipping_date', '-id']


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    service_name = models.CharField("Наименование услуги", max_length=200, default="Услуга по доставке товара")
    product_name = models.CharField("Наименование товара клиента", max_length=255)
    places_count = models.PositiveIntegerField("Количество мест", default=1)
    units_count = models.PositiveIntegerField("Количество шт.", default=1)
    weight = models.DecimalField("Общий вес, кг", max_digits=10, decimal_places=2)
    service_price = models.DecimalField("Стоимость услуги", max_digits=10, decimal_places=2)
    is_fixed_price = models.BooleanField("Фиксированная цена", default=False)
    total_amount = models.DecimalField("Сумма", max_digits=15, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        # Fixed price: total = service_price as-is
        # Per-kg price: total = weight × service_price
        if self.is_fixed_price:
            self.total_amount = self.service_price
        else:
            self.total_amount = self.weight * self.service_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment_id} - {self.product_name}"

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"


class ShipmentExpense(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='expenses', verbose_name="Заказ")
    name = models.CharField("Номенклатура", max_length=255)
    quantity = models.PositiveIntegerField("Количество", default=1)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    total_amount = models.DecimalField("Сумма", max_digits=15, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment_id} - {self.name}"

    class Meta:
        verbose_name = "Дополнительный расход"
        verbose_name_plural = "Дополнительные расходы"

class ShipmentStatusHistory(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='history', verbose_name="Заказ")
    old_status = models.CharField("Старый статус", max_length=20, choices=ShipmentStatus.choices, null=True, blank=True)
    new_status = models.CharField("Новый статус", max_length=20, choices=ShipmentStatus.choices)
    changed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Кто изменил")
    changed_at = models.DateTimeField("Дата изменения", auto_now_add=True)

    def __str__(self):
        return f"История {self.shipment.id}: {self.old_status} -> {self.new_status}"

    class Meta:
        verbose_name = "История статуса"
        verbose_name_plural = "История статусов"
        ordering = ['-changed_at']


class PriceTier(models.Model):
    min_weight = models.DecimalField("От (кг)", max_digits=10, decimal_places=2, default=0)
    max_weight = models.DecimalField("До (кг)", max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text="Оставьте пустым для последнего тарифа (∞)")
    price = models.DecimalField("Цена (сом)", max_digits=10, decimal_places=2, default=0)
    is_per_kg = models.BooleanField("За каждый кг", default=False,
                                    help_text="Если включено — цена × вес. Иначе — фиксированная сумма.")
    # Legacy field kept for backward compat, will be removed after migration
    price_per_kg = models.DecimalField("Цена за кг (устар.)", max_digits=10, decimal_places=2, default=0)

    def get_price_for_weight(self, weight):
        """Return total price for given weight using this tier's pricing rule."""
        if self.is_per_kg:
            return float(self.price) * float(weight)
        return float(self.price)

    def __str__(self):
        if self.is_per_kg:
            return f"От {self.min_weight} кг — {self.price} сом/кг"
        max_label = f"{self.max_weight} кг" if self.max_weight else "∞"
        return f"До {max_label} — {self.price} сом (фикс.)"

    class Meta:
        verbose_name = "Тариф по весу"
        verbose_name_plural = "Тарифы по весу"
        ordering = ['min_weight', 'max_weight']
