from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Sum

from .models import Product, Customer, SalesOrder, SalesOrderItem, StockMovement


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    fields = ("product", "qty", "price", "line_total")
    readonly_fields = ("line_total",)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "status", "total_amount", "order_date")
    inlines = [SalesOrderItemInline]
    readonly_fields = ("total_amount",)

    def save_model(self, request, obj, form, change):
        obj._old_status = None
        if change and obj.pk:
            obj._old_status = SalesOrder.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        order = form.instance

        total = order.items.aggregate(total=Sum("line_total"))["total"] or 0
        order.total_amount = total
        order.save(update_fields=["total_amount"])

        old_status = getattr(order, "_old_status", None) or SalesOrder.STATUS_PENDING
        new_status = order.status

        try:
            if old_status != SalesOrder.STATUS_CONFIRMED and new_status == SalesOrder.STATUS_CONFIRMED:
                order.confirm(user=request.user)

            elif old_status == SalesOrder.STATUS_CONFIRMED and new_status == SalesOrder.STATUS_CANCELLED:
                order.cancel(user=request.user)

        except ValidationError as e:
            order.status = old_status
            order.save(update_fields=["status"])
            messages.error(request, f"Order status failed: {e}")


admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(StockMovement)
