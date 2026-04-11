import openpyxl
from django.contrib import admin
from django.db.models import Sum
from django.http import HttpResponse
from .models import Shipment, ShipmentStatusHistory

class ShipmentStatusHistoryInline(admin.TabularInline):
    model = ShipmentStatusHistory
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'changed_at')
    extra = 0
    can_delete = False
    verbose_name = "История изменения статуса"
    verbose_name_plural = "История изменений статусов"

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'weight', 'price_per_kg', 'total_price', 'status', 'shipping_date')
    list_filter = ('status', 'shipping_date', 'client')
    search_fields = ('client__client_code', 'client__first_name', 'client__last_name', 'notes')
    readonly_fields = ('total_price', 'shipping_date', 'updated_at')
    inlines = [ShipmentStatusHistoryInline]
    
    actions = ['mark_as_in_transit', 'mark_as_received', 'mark_as_issued', 'export_to_excel']

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Shipment.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                ShipmentStatusHistory.objects.create(
                    shipment=obj,
                    old_status=old_obj.status,
                    new_status=obj.status,
                    changed_by=request.user
                )
        super().save_model(request, obj, form, change)

    def mark_as_in_transit(self, request, queryset):
        for obj in queryset:
            old_status = obj.status
            obj.status = 'in_transit'
            obj.save()
            ShipmentStatusHistory.objects.create(
                shipment=obj,
                old_status=old_status,
                new_status='in_transit',
                changed_by=request.user
            )
    mark_as_in_transit.short_description = "Отметить как 'В пути'"

    def mark_as_received(self, request, queryset):
        for obj in queryset:
            old_status = obj.status
            obj.status = 'received'
            obj.save()
            ShipmentStatusHistory.objects.create(
                shipment=obj,
                old_status=old_status,
                new_status='received',
                changed_by=request.user
            )
    mark_as_received.short_description = "Отметить как 'Получено (в РФ)'"

    def mark_as_issued(self, request, queryset):
        for obj in queryset:
            old_status = obj.status
            obj.status = 'issued'
            obj.save()
            ShipmentStatusHistory.objects.create(
                shipment=obj,
                old_status=old_status,
                new_status='issued',
                changed_by=request.user
            )
    mark_as_issued.short_description = "Отметить как 'Выдано клиенту'"

    def export_to_excel(self, request, queryset):
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Shipments"

        # Define columns
        columns = ['ID', 'Код Клиента', 'Клиент', 'Вес (кг)', 'Цена/кг', 'Итого', 'Статус', 'Дата']
        ws.append(columns)

        # Add data
        for obj in queryset:
            ws.append([
                obj.id,
                obj.client.client_code,
                f"{obj.client.first_name} {obj.client.last_name}",
                obj.weight,
                obj.price_per_kg,
                obj.total_price,
                obj.get_status_display(),
                obj.shipping_date.strftime("%d.%m.%Y")
            ])

        # Prepare response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="shipments_report.xlsx"'
        wb.save(response)
        return response
    export_to_excel.short_description = "Экспорт в Excel (.xlsx)"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total_weight': qs.aggregate(Sum('weight'))['weight__sum'] or 0,
            'total_revenue': qs.aggregate(Sum('total_price'))['total_price__sum'] or 0,
            'shipment_count': qs.count(),
        }
        
        response.context_data['summary_metrics'] = metrics
        return response
