from django.contrib import admin
from .models import Profile, Bill, WaterUsage,  Payment  # import your model

admin.site.register(Profile)  
admin.site.register(Bill)
admin.site.register(WaterUsage)
admin.site.register(Payment)