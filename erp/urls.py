from django.urls import path

from .views import (
    ProductListAPIView, ProductCreateAPIView, ProductRetrieveAPIView,
    ProductUpdateAPIView, ProductDeleteAPIView,
    CustomerListAPIView, CustomerCreateAPIView, CustomerRetrieveAPIView,
    CustomerUpdateAPIView, CustomerDeleteAPIView,
    SalesOrderListAPIView, SalesOrderCreateAPIView, SalesOrderRetrieveAPIView,
    SalesOrderUpdateAPIView, SalesOrderDeleteAPIView,
    StockMovementListAPIView, StockMovementRetrieveAPIView,
    UserRegisterAPIView,
)


urlpatterns = [
    path("auth/register/", UserRegisterAPIView.as_view(), name="register"),
    path("products/", ProductListAPIView.as_view()),
    path("products/create/", ProductCreateAPIView.as_view()),
    path("products/<int:pk>/", ProductRetrieveAPIView.as_view()),
    path("products/<int:pk>/update/", ProductUpdateAPIView.as_view()),
    path("products/<int:pk>/delete/", ProductDeleteAPIView.as_view()),
    path("customers/", CustomerListAPIView.as_view()),
    path("customers/create/", CustomerCreateAPIView.as_view()),
    path("customers/<int:pk>/", CustomerRetrieveAPIView.as_view()),
    path("customers/<int:pk>/update/", CustomerUpdateAPIView.as_view()),
    path("customers/<int:pk>/delete/", CustomerDeleteAPIView.as_view()),
    path("orders/", SalesOrderListAPIView.as_view()),
    path("orders/create/", SalesOrderCreateAPIView.as_view()),
    path("orders/<int:pk>/", SalesOrderRetrieveAPIView.as_view()),
    path("orders/<int:pk>/update/", SalesOrderUpdateAPIView.as_view()),
    path("orders/<int:pk>/delete/", SalesOrderDeleteAPIView.as_view()),
    path("stock-movements/", StockMovementListAPIView.as_view()),
    path("stock-movements/<int:pk>/", StockMovementRetrieveAPIView.as_view()),
]
