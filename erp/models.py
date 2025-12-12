from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError



class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Customer(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


class SalesOrder(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    order_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = get_random_string(10).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number
    
    @transaction.atomic
    def confirm(self, user=None):
        items = self.items.select_related("product").all()

        for item in items:
            if item.product.stock_qty < item.qty:
                raise ValidationError(
                    f"Not enough stock for product {item.product.sku}. "
                    f"Available={item.product.stock_qty}, Requested={item.qty}"
                )

        for item in items:
            product = item.product
            product.stock_qty -= item.qty
            product.save(update_fields=["stock_qty"])

            StockMovement.objects.create(
                product=product,
                qty=-item.qty,
                movement_type=StockMovement.MOVEMENT_SALE,
                user=user,
            )

        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status"])

    @transaction.atomic
    def cancel(self, user=None):
        items = self.items.select_related("product").all()

        for item in items:
            product = item.product
            product.stock_qty += item.qty
            product.save(update_fields=["stock_qty"])

            StockMovement.objects.create(
                product=product,
                qty=item.qty,
                movement_type=StockMovement.MOVEMENT_RETURN,
                user=user,
            )

        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status"])

    def __str__(self):
        return self.order_number



    
from decimal import Decimal


class SalesOrderItem(models.Model):
    order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)


    def save(self, *args, **kwargs):
        self.line_total = Decimal(self.price) * Decimal(self.qty)
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    MOVEMENT_SALE = "sale"
    MOVEMENT_RETURN = "return"

    MOVEMENT_CHOICES = [
        (MOVEMENT_SALE, "Sale"),
        (MOVEMENT_RETURN, "Return"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stock_movements"
    )
    qty = models.IntegerField()
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product} - {self.qty} ({self.movement_type})"
