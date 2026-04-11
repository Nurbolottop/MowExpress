import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.users.models import ClientProfile
from apps.logistics.models import Shipment, ShipmentStatus

def create_test_data():
    # Create test client
    client, created = ClientProfile.objects.get_or_create(
        phone_number="+996111223344",
        defaults={
            'first_name': 'Айбек',
            'last_name': 'Каракетов',
        }
    )
    if created:
        print(f"Создан клиент: {client.first_name} (Код: {client.client_code})")
    else:
        print(f"Клиент уже существует: {client.first_name} (Код: {client.client_code})")

    # Create test shipment
    shipment = Shipment.objects.create(
        client=client,
        weight=random.uniform(5.0, 50.0),
        price_per_kg=60,
        status=ShipmentStatus.SENT,
        notes="Тестовый заказ через скрипт"
    )
    print(f"Создана отправка №{shipment.id} для кода {client.client_code}")

if __name__ == "__main__":
    create_test_data()
