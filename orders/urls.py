from django.urls import path
from . import views

app_name = 'orders'  # IMPORTANT: Ensure app_name is set

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('track-order/', views.track_order, name='track_order'),  # ✅ Add this line
   # path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('success/', views.order_success, name='order_success'),
    path('invoice/<int:order_id>/', views.invoice_view, name='invoice'),
    path('invoice/<int:order_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback')


]
