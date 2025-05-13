from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import User, Bill, WaterUsage, Payment
from datetime import datetime, timedelta
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.db.models import Sum
import json

# ADMIN SIDE
@login_required
def admin_settings(request):
    if not request.user.is_superuser:
        return redirect('settings')
    
    return render(request, 'admin/settings.html', {
        'user': request.user
    })



@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    total_users = User.objects.count()
    total_revenue = sum(b.amount for b in Bill.objects.filter(status='paid'))
    pending_bills = Bill.objects.filter(status='pending')
    total_consumption = sum(u.consumption_liters for u in WaterUsage.objects.all())

    # Monthly Revenue (assuming Bill.created_at exists)
    monthly_revenue = (
        Bill.objects.filter(status='paid')
        .annotate(month=TruncMonth('created_at'))  # keep if Bill has created_at
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    revenue_labels = [item['month'].strftime('%B') for item in monthly_revenue]
    revenue_values = [float(item['total']) for item in monthly_revenue]

    # Monthly Consumption (use WaterUsage.date)
    monthly_consumption = (
        WaterUsage.objects
        .annotate(month=TruncMonth('date'))  # fixed here
        .values('month')
        .annotate(total=Sum('consumption_liters'))
        .order_by('month')
    )
    consumption_labels = [item['month'].strftime('%B') for item in monthly_consumption]
    consumption_values = [float(item['total']) for item in monthly_consumption]

    context = {
        'total_users': total_users,
        'total_revenue': total_revenue,
        'pending_bills': pending_bills,
        'total_consumption': total_consumption,
        'revenue_labels_json': json.dumps(revenue_labels),
        'revenue_values_json': json.dumps(revenue_values),
        'consumption_labels_json': json.dumps(consumption_labels),
        'consumption_values_json': json.dumps(consumption_values),
    }

    return render(request, 'admin/dashboard.html', context)

@login_required
def paid_consumers(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    paid_bills = Bill.objects.filter(status='paid').select_related('user')

    return render(request, 'admin/paid_consumers.html', {
        'paid_bills': paid_bills
    })

@login_required
def input_water_reading(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    # Initialize previous_reading to None to handle GET requests
    previous_reading = None

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        current_reading = request.POST.get('current_reading')

        # Check if user_id or current_reading is not provided
        if not user_id:
            messages.error(request, "Please select a user.")
            return render(request, 'admin/billing_management.html', {
                'users': User.objects.filter(is_superuser=False),
                'previous_reading': previous_reading
            })

        if not current_reading:
            messages.error(request, "Please enter the current reading.")
            return render(request, 'admin/billing_management.html', {
                'users': User.objects.filter(is_superuser=False),
                'previous_reading': previous_reading
            })

        # Convert current reading to float
        current_reading = float(current_reading)

        user = User.objects.get(id=user_id)
        last_usage = WaterUsage.objects.filter(user=user).order_by('-date').first()
        previous_reading = float(last_usage.consumption_liters) if last_usage else 0

        # Prevent negative consumption (current reading must not be less than previous reading)
        if current_reading < previous_reading:
            messages.error(request, "Current reading cannot be less than the previous reading. Water usage cannot go backwards.")
            return render(request, 'admin/billing_management.html', {
                'users': User.objects.filter(is_superuser=False),
                'previous_reading': previous_reading
            })

        # Calculate the consumption and generate the bill
        consumption = current_reading - previous_reading

        WaterUsage.objects.create(user=user, consumption_liters=current_reading)

        bill_amount = 50 + (consumption * 30)  # base + per m³ (50 is the base rate, 30 cost per m³)
        Bill.objects.create(
            user=user,
            period=datetime.now().strftime("%B %Y"),
            amount=bill_amount,
            consumption_m3=consumption,
            rate_per_m3=30,
            status='unpaid',
            due_date=datetime.now() + timedelta(days=15)
        )
        messages.success(request, f"Bill generated for {user.username}")

    users = User.objects.filter(is_superuser=False)
    return render(request, 'admin/billing_management.html', {'users': users, 'previous_reading': previous_reading})

@login_required
def verify_payments(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    pending_bills = Bill.objects.filter(status='pending')
    bills_with_payment_info = []

    for bill in pending_bills:
        payment = Payment.objects.filter(bill=bill).first()
        bills_with_payment_info.append({
            'bill': bill,
            'payment': payment
        })

    if request.method == 'POST':
        bill_id = request.POST.get('bill_id')
        action = request.POST.get('action')  # 'verify' or 'reject'

        try:
            bill = Bill.objects.get(id=bill_id)
            payment = Payment.objects.filter(bill=bill).first()

            if not payment:
                messages.error(request, "No payment record found for this bill.")
                return redirect('verify_payments')

            if action == 'verify':
                bill.status = 'paid'
                bill.save()
                messages.success(request, "Payment verified successfully.")

            elif action == 'reject':
                bill.status = 'unpaid'
                bill.save()
                payment.delete()  # Optional: remove the payment record
                messages.warning(request, "Payment has been rejected and set back to unpaid.")

        except Bill.DoesNotExist:
            messages.error(request, "Bill not found.")

        return redirect('verify_payments')

    return render(request, 'admin/verify_payments.html', {
        'bills_with_payment_info': bills_with_payment_info
    })
