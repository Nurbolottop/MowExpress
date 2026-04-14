from django.shortcuts import render, get_object_or_404
from .models import Shipment
from apps.users.models import ClientProfile

def index(request):
    """Главная страница (редирект на отслеживание)"""
    return render(request, 'index.html')

def tracking_view(request):
    """Страница отслеживания отправки по коду клиента или номеру накладной"""
    client_code = request.GET.get('code')
    shipments = None
    client = None
    error = None

    if client_code:
        # Сначала ищем по номеру накладной
        waybill_shipments = Shipment.objects.filter(waybill_number=client_code)
        if waybill_shipments.exists():
            shipments = waybill_shipments
            client = waybill_shipments.first().client
        else:
            try:
                client = ClientProfile.objects.get(client_code=client_code)
                shipments = client.shipments.all()
            except ClientProfile.DoesNotExist:
                error = "Отправка не найдена. Проверьте код клиента или номер накладной."

    return render(request, 'logistics/tracking.html', {
        'shipments': shipments,
        'client': client,
        'error': error,
        'client_code': client_code
    })

def shipment_print_view(request, pk):
    """Печатная форма (Накладной лист)"""
    shipment = get_object_or_404(
        Shipment.objects.prefetch_related('items', 'expenses').select_related('client'),
        pk=pk
    )
    from apps.base.models import SiteSettings
    settings = SiteSettings.load()
    tracking_url = request.build_absolute_uri(f'/tracking/?code={shipment.waybill_number}')
    return render(request, 'logistics/shipment_print.html', {
        'shipment': shipment,
        'settings': settings,
        'tracking_url': tracking_url,
    })
