from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# User profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return self.user.username

# Billing record
class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.CharField(max_length=20)  # e.g., 'April 2025'
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in dollars
    status = models.CharField(max_length=10, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')], default='unpaid')
    due_date = models.DateField()

    def __str__(self):
        return f"Bill for {self.period} - {self.status}"

# Water usage
class WaterUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    consumption_liters = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.consumption_liters}L"

# Payments
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} via {self.payment_method}"
