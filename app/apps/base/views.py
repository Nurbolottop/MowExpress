from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.logistics.models import PriceTier, Shipment, ShipmentCategory, ShipmentExpense, ShipmentItem, ShipmentStatus, ShipmentStatusHistory
from apps.users.models import ClientProfile

from .forms import ClientForm, ShipmentExpenseForm, ShipmentForm, ShipmentItemForm, ShipmentStatusForm


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def manager_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('manager_dashboard')

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if not user.is_staff:
            messages.error(request, 'Доступ разрешен только менеджерам.')
        else:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('manager_dashboard')

    return render(request, 'crm/login.html', {'form': form})


@login_required(login_url='manager_login')
def manager_logout_view(request):
    logout(request)
    return redirect('manager_login')


def _is_manager(user):
    return user.is_authenticated and user.is_staff


STATUS_FLOW = [
    ShipmentStatus.SENT,
    ShipmentStatus.IN_TRANSIT,
    ShipmentStatus.RECEIVED,
    ShipmentStatus.ISSUED,
]


def _get_status_steps(current_status):
    status_labels = dict(ShipmentStatus.choices)
    try:
        current_index = STATUS_FLOW.index(current_status)
    except ValueError:
        current_index = 0

    steps = []
    for idx, status_code in enumerate(STATUS_FLOW):
        steps.append({
            'code': status_code,
            'label': status_labels.get(status_code, status_code),
            'is_done': idx < current_index,
            'is_current': idx == current_index,
        })
    return steps, current_index


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@user_passes_test(_is_manager, login_url='manager_login')
def manager_dashboard_view(request):
    shipments = Shipment.objects.select_related('client').all()

    context = {
        'active_page': 'dashboard',
        'shipment_count': shipments.count(),
        'client_count': ClientProfile.objects.count(),
        'active_clients_count': ClientProfile.objects.filter(
            shipments__isnull=False
        ).distinct().count(),
        'total_revenue': shipments.aggregate(
            total=Sum('total_price')
        )['total'] or 0,
        'recent_shipments': shipments.order_by('-shipping_date', '-id')[:7],
        'status_counts': {
            'sent': shipments.filter(status=ShipmentStatus.SENT).count(),
            'in_transit': shipments.filter(status=ShipmentStatus.IN_TRANSIT).count(),
            'received': shipments.filter(status=ShipmentStatus.RECEIVED).count(),
            'issued': shipments.filter(status=ShipmentStatus.ISSUED).count(),
        },
    }
    return render(request, 'crm/dashboard.html', context)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@user_passes_test(_is_manager, login_url='manager_login')
def manager_profile_view(request):
    return render(request, 'crm/profile.html', {'active_page': 'profile'})


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

@user_passes_test(_is_manager, login_url='manager_login')
def manager_clients_view(request):
    query = request.GET.get('q', '').strip()
    clients = ClientProfile.objects.all()

    if query:
        clients = clients.filter(
            Q(client_code__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone_number__icontains=query)
        )

    clients = clients.annotate(
        shipment_total=Count('shipments')
    ).order_by('-created_at')

    return render(request, 'crm/clients.html', {
        'active_page': 'clients',
        'clients': clients,
        'query': query,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_client_detail_view(request, pk):
    client = get_object_or_404(ClientProfile, pk=pk)
    shipments = client.shipments.all().order_by('-shipping_date', '-id')

    return render(request, 'crm/client_detail.html', {
        'active_page': 'clients',
        'client': client,
        'shipments': shipments,
        'total_spent': shipments.aggregate(t=Sum('total_price'))['t'] or 0,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_client_create_view(request):
    form = ClientForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        client = form.save()
        messages.success(
            request,
            f'Клиент {client.first_name} {client.last_name} создан. Код: {client.client_code}',
        )
        return redirect('manager_client_detail', pk=client.pk)

    return render(request, 'crm/client_create.html', {
        'active_page': 'client_create',
        'form': form,
    })


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------

@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipments_view(request):
    status_filter = request.GET.get('status', '').strip()
    code_filter = request.GET.get('code', '').strip()
    category_filter = request.GET.get('category', '').strip()

    shipments = Shipment.objects.select_related('client').all()
    valid_statuses = {v for v, _ in ShipmentStatus.choices}
    valid_categories = {v for v, _ in ShipmentCategory.choices}

    if status_filter in valid_statuses:
        shipments = shipments.filter(status=status_filter)
    if category_filter in valid_categories:
        shipments = shipments.filter(category=category_filter)
    if code_filter:
        shipments = shipments.filter(client__client_code__icontains=code_filter)

    shipments = shipments.order_by('-shipping_date', '-id')

    return render(request, 'crm/shipments.html', {
        'active_page': 'shipments',
        'shipments': shipments,
        'status_choices': ShipmentStatus.choices,
        'category_choices': ShipmentCategory.choices,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'code_filter': code_filter,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_detail_view(request, pk):
    shipment = get_object_or_404(
        Shipment.objects.select_related('client').prefetch_related('items', 'expenses'), pk=pk
    )
    history = shipment.history.select_related('changed_by').order_by('-changed_at')
    status_steps, current_index = _get_status_steps(shipment.status)

    return render(request, 'crm/shipment_detail.html', {
        'active_page': 'shipments',
        'shipment': shipment,
        'history': history,
        'status_steps': status_steps,
        'next_status_steps': status_steps[current_index + 1:],
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_create_view(request):
    initial_code = request.GET.get('code', '')
    form = ShipmentForm(request.POST or None, initial={'client_code': initial_code})
    item_form = ShipmentItemForm()
    expense_form = ShipmentExpenseForm()

    if request.method == 'POST' and form.is_valid():
        service_names = request.POST.getlist('item_service_name[]')
        product_names = request.POST.getlist('item_product_name[]')
        places_counts = request.POST.getlist('item_places_count[]')
        units_counts = request.POST.getlist('item_units_count[]')
        item_weights = request.POST.getlist('item_weight[]')
        service_prices = request.POST.getlist('item_service_price[]')

        expense_names = request.POST.getlist('expense_name[]')
        expense_quantities = request.POST.getlist('expense_quantity[]')
        expense_prices = request.POST.getlist('expense_price[]')

        item_rows = []
        for idx, product_name in enumerate(product_names):
            if not product_name.strip():
                continue
            try:
                item_rows.append({
                    'service_name': (service_names[idx] or 'Услуга по доставке товара').strip(),
                    'product_name': product_name.strip(),
                    'places_count': int(places_counts[idx] or 1),
                    'units_count': int(units_counts[idx] or 1),
                    'weight': Decimal((item_weights[idx] or '0').replace(',', '.')),
                    'service_price': Decimal((service_prices[idx] or '0').replace(',', '.')),
                })
            except (IndexError, ValueError, InvalidOperation):
                messages.error(request, 'Проверьте заполнение товарных позиций.')
                return render(request, 'crm/shipment_create.html', {
                    'active_page': 'shipment_create',
                    'form': form,
                    'item_form': item_form,
                    'expense_form': expense_form,
                })

        if not item_rows:
            messages.error(request, 'Добавьте хотя бы одну товарную позицию.')
            return render(request, 'crm/shipment_create.html', {
                'active_page': 'shipment_create',
                'form': form,
                'item_form': item_form,
                'expense_form': expense_form,
            })

        expense_rows = []
        for idx, name in enumerate(expense_names):
            if not name.strip():
                continue
            try:
                expense_rows.append({
                    'name': name.strip(),
                    'quantity': int(expense_quantities[idx] or 1),
                    'price': Decimal((expense_prices[idx] or '0').replace(',', '.')),
                })
            except (IndexError, ValueError, InvalidOperation):
                messages.error(request, 'Проверьте заполнение дополнительных расходов.')
                return render(request, 'crm/shipment_create.html', {
                    'active_page': 'shipment_create',
                    'form': form,
                    'item_form': item_form,
                    'expense_form': expense_form,
                })

        with transaction.atomic():
            client = ClientProfile.objects.get(
                client_code=form.cleaned_data['client_code']
            )
            shipment = form.save(commit=False)
            shipment.client = client
            shipment.weight = 0
            shipment.price_per_kg = 0
            shipment.total_price = 0
            shipment.save()

            for row in item_rows:
                ShipmentItem.objects.create(shipment=shipment, **row)

            for row in expense_rows:
                ShipmentExpense.objects.create(shipment=shipment, **row)

            shipment.recalculate_totals()

            ShipmentStatusHistory.objects.create(
                shipment=shipment,
                old_status=None,
                new_status=shipment.status,
                changed_by=request.user,
            )

        messages.success(request, f'Заказ #{shipment.id} успешно создан.')
        return redirect('manager_shipment_detail', pk=shipment.pk)

    return render(request, 'crm/shipment_create.html', {
        'active_page': 'shipment_create',
        'form': form,
        'item_form': item_form,
        'expense_form': expense_form,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_edit_view(request, pk):
    shipment = get_object_or_404(
        Shipment.objects.select_related('client').prefetch_related('items', 'expenses'), pk=pk
    )
    form = ShipmentForm(
        request.POST or None,
        instance=shipment,
        initial={'client_code': shipment.client.client_code},
    )

    if request.method == 'POST' and form.is_valid():
        service_names = request.POST.getlist('item_service_name[]')
        product_names = request.POST.getlist('item_product_name[]')
        places_counts = request.POST.getlist('item_places_count[]')
        units_counts = request.POST.getlist('item_units_count[]')
        item_weights = request.POST.getlist('item_weight[]')
        service_prices = request.POST.getlist('item_service_price[]')

        expense_names = request.POST.getlist('expense_name[]')
        expense_quantities = request.POST.getlist('expense_quantity[]')
        expense_prices = request.POST.getlist('expense_price[]')

        item_rows = []
        for idx, product_name in enumerate(product_names):
            if not product_name.strip():
                continue
            try:
                item_rows.append({
                    'service_name': (service_names[idx] or 'Услуга по доставке товара').strip(),
                    'product_name': product_name.strip(),
                    'places_count': int(places_counts[idx] or 1),
                    'units_count': int(units_counts[idx] or 1),
                    'weight': Decimal((item_weights[idx] or '0').replace(',', '.')),
                    'service_price': Decimal((service_prices[idx] or '0').replace(',', '.')),
                })
            except (IndexError, ValueError, InvalidOperation):
                messages.error(request, 'Проверьте заполнение товарных позиций.')
                return render(request, 'crm/shipment_edit.html', {
                    'active_page': 'shipments',
                    'form': form,
                    'shipment': shipment,
                })

        if not item_rows:
            messages.error(request, 'Добавьте хотя бы одну товарную позицию.')
            return render(request, 'crm/shipment_edit.html', {
                'active_page': 'shipments',
                'form': form,
                'shipment': shipment,
            })

        expense_rows = []
        for idx, name in enumerate(expense_names):
            if not name.strip():
                continue
            try:
                expense_rows.append({
                    'name': name.strip(),
                    'quantity': int(expense_quantities[idx] or 1),
                    'price': Decimal((expense_prices[idx] or '0').replace(',', '.')),
                })
            except (IndexError, ValueError, InvalidOperation):
                messages.error(request, 'Проверьте заполнение дополнительных расходов.')
                return render(request, 'crm/shipment_edit.html', {
                    'active_page': 'shipments',
                    'form': form,
                    'shipment': shipment,
                })

        with transaction.atomic():
            client = ClientProfile.objects.get(
                client_code=form.cleaned_data['client_code']
            )
            shipment = form.save(commit=False)
            shipment.client = client
            shipment.save()

            shipment.items.all().delete()
            shipment.expenses.all().delete()

            for row in item_rows:
                ShipmentItem.objects.create(shipment=shipment, **row)

            for row in expense_rows:
                ShipmentExpense.objects.create(shipment=shipment, **row)

            shipment.recalculate_totals()

        messages.success(request, f'Заказ #{shipment.id} успешно обновлён.')
        return redirect('manager_shipment_detail', pk=shipment.pk)

    return render(request, 'crm/shipment_edit.html', {
        'active_page': 'shipments',
        'form': form,
        'shipment': shipment,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_status_view(request, pk):
    shipment = get_object_or_404(
        Shipment.objects.select_related('client'), pk=pk
    )
    form = ShipmentStatusForm(
        request.POST or None,
        initial={'status': shipment.status},
    )

    if request.method == 'POST' and form.is_valid():
        new_status = form.cleaned_data['status']
        if new_status != shipment.status:
            old_status = shipment.status
            shipment.status = new_status
            shipment.save()

            ShipmentStatusHistory.objects.create(
                shipment=shipment,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
            )
            messages.success(request, 'Статус заказа обновлен.')
        else:
            messages.info(request, 'Статус не изменился.')

        return redirect('manager_shipment_detail', pk=shipment.pk)

    return render(request, 'crm/shipment_status.html', {
        'active_page': 'shipments',
        'shipment': shipment,
        'form': form,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_status_quick_update_view(request, pk):
    if request.method != 'POST':
        return redirect('manager_shipment_detail', pk=pk)

    shipment = get_object_or_404(Shipment.objects.select_related('client'), pk=pk)
    new_status = request.POST.get('status')
    status_steps, current_index = _get_status_steps(shipment.status)
    allowed_statuses = [step['code'] for step in status_steps[current_index + 1:]]

    if new_status not in allowed_statuses:
        messages.error(request, 'Можно выбрать только следующий этап процесса.')
        return redirect('manager_shipment_detail', pk=shipment.pk)

    old_status = shipment.status
    shipment.status = new_status
    shipment.save(update_fields=['status', 'updated_at'])

    ShipmentStatusHistory.objects.create(
        shipment=shipment,
        old_status=old_status,
        new_status=new_status,
        changed_by=request.user,
    )
    messages.success(request, f'Статус обновлён: {shipment.get_status_display()}.')
    return redirect('manager_shipment_detail', pk=shipment.pk)


from django.urls import reverse

@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_print_view(request, pk):
    shipment = get_object_or_404(
        Shipment.objects.select_related('client').prefetch_related('items', 'expenses'), pk=pk
    )
    items = list(shipment.items.all())
    expenses = list(shipment.expenses.all())
    total_places = sum(item.places_count for item in items)
    total_units = sum(item.units_count for item in items)
    total_expense_quantity = sum(expense.quantity for expense in expenses)
    total_expense_amount = sum(expense.total_amount for expense in expenses)
    items_total = sum(item.total_amount for item in items)
    grand_total = items_total + total_expense_amount
    tracking_url = request.build_absolute_uri(
        f"{reverse('tracking')}?code={shipment.waybill_number}"
    )
    return render(request, 'crm/shipment_print.html', {
        'shipment': shipment,
        'total_places': total_places,
        'total_units': total_units,
        'total_expense_quantity': total_expense_quantity,
        'total_expense_amount': total_expense_amount,
        'items_total': items_total,
        'grand_total': grand_total,
        'tracking_url': tracking_url,
    })


@user_passes_test(_is_manager, login_url='manager_login')
def manager_shipment_sticker_view(request, pk):
    shipment = get_object_or_404(
        Shipment.objects.select_related('client').prefetch_related('items', 'expenses'), pk=pk
    )
    return render(request, 'crm/shipment_sticker.html', {'shipment': shipment})


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@user_passes_test(_is_manager, login_url='manager_login')
def manager_analytics_view(request):
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    shipments = Shipment.objects.select_related('client').all()

    if date_from:
        shipments = shipments.filter(shipping_date__gte=date_from)
    if date_to:
        shipments = shipments.filter(shipping_date__lte=date_to)

    total_revenue = shipments.aggregate(t=Sum('total_price'))['t'] or 0
    total_weight = shipments.aggregate(t=Sum('weight'))['t'] or 0

    context = {
        'active_page': 'analytics',
        'date_from': date_from,
        'date_to': date_to,
        'shipment_count': shipments.count(),
        'total_revenue': total_revenue,
        'total_weight': total_weight,
        'client_count': ClientProfile.objects.count(),
        'active_clients': (
            shipments.values('client')
            .distinct()
            .count()
        ),
        'status_counts': {
            'sent': shipments.filter(status=ShipmentStatus.SENT).count(),
            'in_transit': shipments.filter(status=ShipmentStatus.IN_TRANSIT).count(),
            'received': shipments.filter(status=ShipmentStatus.RECEIVED).count(),
            'issued': shipments.filter(status=ShipmentStatus.ISSUED).count(),
        },
        'recent_shipments': shipments.order_by('-shipping_date', '-id')[:10],
    }
    return render(request, 'crm/analytics.html', context)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@user_passes_test(_is_manager, login_url='manager_login')
def manager_settings_view(request):
    if request.method == 'POST':
        # Clear existing tiers and re-create from form
        max_weights = request.POST.getlist('tier_max_weight[]')
        prices = request.POST.getlist('tier_price_per_kg[]')
        tiers = []
        for mw, pr in zip(max_weights, prices):
            mw = mw.strip().replace(',', '.')
            pr = pr.strip().replace(',', '.')
            if not mw or not pr:
                continue
            try:
                tiers.append({
                    'max_weight': Decimal(mw),
                    'price_per_kg': Decimal(pr),
                })
            except (InvalidOperation, ValueError):
                messages.error(request, 'Проверьте правильность введённых данных.')
                return redirect('manager_settings')
        PriceTier.objects.all().delete()
        for t in tiers:
            PriceTier.objects.create(**t)
        messages.success(request, 'Тарифы сохранены.')
        return redirect('manager_settings')

    tiers = PriceTier.objects.all()
    return render(request, 'crm/settings.html', {
        'active_page': 'settings',
        'tiers': tiers,
    })


from django.http import JsonResponse

@user_passes_test(_is_manager, login_url='manager_login')
def api_price_tiers(request):
    tiers = list(PriceTier.objects.order_by('max_weight').values('max_weight', 'price_per_kg'))
    return JsonResponse(tiers, safe=False)
