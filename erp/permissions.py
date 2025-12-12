from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists()


def is_sales(user):
    return user.groups.filter(name="Sales").exists()


class ProductPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return is_admin(request.user)

class CustomerPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method == "DELETE":
            return is_admin(request.user)

        return is_admin(request.user) or is_sales(request.user)


class SalesOrderPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return is_admin(request.user) or is_sales(request.user)
