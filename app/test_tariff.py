import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.logistics.models import PriceTier
from decimal import Decimal

# Test 1: Let's see the tiers in db
tiers = PriceTier.objects.order_by('min_weight')
for t in tiers:
    print(f"Tier: min={t.min_weight}, max={t.max_weight}, price={t.price}, per_kg={t.is_per_kg}")

weight_str = '3'
weight = Decimal(weight_str) if weight_str else Decimal('0')

price = Decimal('0')
is_per_kg = True

for t in tiers:
    max_w = t.max_weight if t.max_weight is not None else Decimal('inf')
    if weight <= max_w:
        price = t.price
        is_per_kg = t.is_per_kg
        break

print(f"Calc: weight={weight}, price={price}, is_per_kg={is_per_kg}")

