from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Product, Customer, SalesOrder, SalesOrderItem, StockMovement

from django.contrib.auth.models import User, Group
from rest_framework import serializers

class   UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    group = serializers.ChoiceField(
        choices=[("Admin", "Admin"), ("Sales", "Sales")],
        required=False,
        help_text="Optional: choose role group (Admin or Sales)"
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "group"]

    def create(self, validated_data):
        group_name = validated_data.pop("group", None)
        password = validated_data.pop("password")

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

        return user



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = SalesOrderItem
        fields = ["id", "product", "product_name", "qty", "price", "line_total"]
        read_only_fields = ["line_total"]

    def validate(self, attrs):
        product = attrs["product"]
        qty = attrs["qty"]
        if qty <= 0:
            raise serializers.ValidationError("Qty must be > 0")
        return attrs


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_name",
            "qty",
            "movement_type",
            "username",
            "timestamp",
        ]

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = ["id", "order_number", "customer", "order_date", "status", "total_amount", "items"]
        read_only_fields = ["order_number", "total_amount"]

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user

        order = SalesOrder.objects.create(created_by=user, **validated_data)

        total = Decimal("0.00")
        for item in items_data:
            product = item["product"]
            qty = item["qty"]
            price = item.get("price") or product.selling_price

            line_total = Decimal(price) * qty

            SalesOrderItem.objects.create(
                order=order,
                product=product,
                qty=qty,
                price=price,
            )

            total += line_total

        order.total_amount = total
        order.save(update_fields=["total_amount"])

        if order.status == SalesOrder.STATUS_CONFIRMED:
            order.confirm(user=user)

        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context["request"].user
        new_status = validated_data.get("status", instance.status)

        if instance.status != SalesOrder.STATUS_CONFIRMED and new_status == SalesOrder.STATUS_CONFIRMED:
            instance.confirm(user=user)

        elif instance.status == SalesOrder.STATUS_CONFIRMED and new_status == SalesOrder.STATUS_CANCELLED:
            instance.cancel(user=user)

        else:
            instance.status = new_status
            instance.save(update_fields=["status"])

        return instance
