from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0006_shipment_delivery_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_weight', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='До (кг)')),
                ('price_per_kg', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за кг (сом)')),
            ],
            options={
                'verbose_name': 'Тариф по весу',
                'verbose_name_plural': 'Тарифы по весу',
                'ordering': ['max_weight'],
            },
        ),
    ]
