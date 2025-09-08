from django.db import models
from shop.models import Product

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('mixx', 'Mixx by YAS'),
        ('airtel', 'Airtel Money'),
        ('stripe', 'Stripe')
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    phone = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    bank_name = models.CharField(max_length=50, blank=True, null=True)  # Optional for bank transfers
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all()) 


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def get_cost(self):
        return self.price * self.quantity
    

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('awaiting_confirmation', 'Awaiting Confirmation')
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20)  # mpesa, mixx, airtel, stripe, bank
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    response = models.JSONField(blank=True, null=True)  # raw API response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"
    
   
class Bank(models.Model):
    name = models.CharField(max_length=50)         # e.g., CRDB
    logo = models.ImageField(upload_to='bank_logos/', blank=True, null=True)
    account_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    instructions = models.TextField()

    def __str__(self):
        return self.name
