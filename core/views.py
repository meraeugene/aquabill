from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout,authenticate, login
from django.contrib import messages
from allauth.account.models import EmailAddress 
from core.forms import CustomSignupForm  
from allauth.account.utils import send_email_confirmation
from .models import Profile, Bill, WaterUsage, Payment
import json
from django.db.models import Sum
from django.utils import timezone
from cloudinary.uploader import upload

def signup_view(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        
        if form.is_valid():
            user = form.save(request)
            send_email_confirmation(request, user)
            return redirect('account_login')
        else:
            return render(request, 'account/signup.html', {'form': form})
    else:
        form = CustomSignupForm()
    return render(request, 'account/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Both email and password are required.")
            return redirect('account_login')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            email_address = EmailAddress.objects.filter(user=user, email=user.email).first()

            # Check if the user is admin
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')  # Redirect to admin dashboard
            # If the user is not admin, check email verification
            elif email_address and email_address.verified:
                login(request, user)
                return redirect('dashboard')  # Redirect to user dashboard
            else:
                messages.error(request, "Please verify your email before logging in.")
                return redirect('account_login')

        else:
            messages.error(request, "Invalid email or password.")
            return redirect('account_login')
    else:
        return render(request, 'account/login.html')


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    

    usage_entries = WaterUsage.objects.filter(user=request.user).order_by('-date')[:12][::-1]

    total_usage = sum(u.consumption_liters for u in usage_entries)

    usage_labels = [u.date.strftime('%b %Y') for u in usage_entries]
    usage_values = [float(u.consumption_liters) for u in usage_entries] 

    latest_bill = Bill.objects.filter(
        user=request.user,
        status__in=['unpaid', 'pending']
    ).order_by('-due_date').first()

    context = {
        'usage_entries': usage_entries,
        'total_usage': total_usage,
        'usage_labels_json': json.dumps(usage_labels),
        'usage_values_json': json.dumps(usage_values),
        'latest_bill': latest_bill,
    }

    print(context)
    return render(request, 'core/dashboard.html', context)


@login_required
def bills(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    user_bills = Bill.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/bills.html', {
        'bills': user_bills
    })

@login_required
def usage(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    usage_entries = WaterUsage.objects.filter(
        user=request.user,
        date__gte=first_day_of_month
    ).order_by('-date')

    total_consumption = usage_entries.aggregate(Sum('consumption_liters'))['consumption_liters__sum'] or 0

    # Calculate average daily usage for the current month
    days_in_month = (now - first_day_of_month).days + 1
    average_daily_usage = round(total_consumption / days_in_month, 2) if total_consumption and days_in_month > 0 else 0

    # Average monthly usage is simply the total consumption for this month
    average_monthly_usage = round(total_consumption, 2)

    usage_labels = [u.date.strftime('%d %b %Y') for u in usage_entries]  # Show day as well
    usage_values = [float(u.consumption_liters) for u in usage_entries]

    usage_data = [{
        'date': u.date.strftime('%d %b %Y'),
        'consumption': float(u.consumption_liters),
    } for u in usage_entries]

    context = {
        'total_consumption': total_consumption,
        'average_daily_usage': average_daily_usage,
        'average_monthly_usage': average_monthly_usage,
        'usage_data': usage_data,
        'usage_labels_json': json.dumps(usage_labels),
        'usage_values_json': json.dumps(usage_values),
    }

    return render(request, 'core/usage.html', context)

@login_required
def payments(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    latest_bill = Bill.objects.filter(
        user=request.user,
        status__in=['unpaid', 'pending']
    ).order_by('-due_date').first()

    
    if not latest_bill:
        return redirect('dashboard')

    total_bill = latest_bill.amount
    due_date = latest_bill.due_date

    context = {
        'total_bill': total_bill,
        'due_date': due_date,
        'latest_bill': latest_bill,
    }

    return render(request, 'core/payments.html', context)


@login_required
def payment_method_selection(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    latest_bill = Bill.objects.filter(user=request.user, status='unpaid').order_by('-due_date').first()

    if not latest_bill:
        return redirect('dashboard')

    total_bill = latest_bill.amount
    due_date = latest_bill.due_date

    context = {
        'total_bill': total_bill,
        'due_date': due_date,
    }

    return render(request, 'core/payment_method_selection.html', context)

@login_required
def ewallet_payment(request):
    latest_bill = Bill.objects.filter(user=request.user, status='unpaid').order_by('-due_date').first()

    if not latest_bill:
        return redirect('dashboard')

    if request.method == 'POST' and request.FILES.get('receipt'):
        # Upload the image manually to a specific folder
        result = upload(
            request.FILES['receipt'],
            folder=f"aquabill/receipts"
        )
        # Create a new Payment record
        payment = Payment(
            user=request.user,
            bill=latest_bill,
            amount=latest_bill.amount,
            payment_method="E-Wallet",  # You can adjust this if needed
            receipt=request.FILES['receipt']
        )
        payment.save()

        # Update the bill's status to 'pending'
        latest_bill.status = 'pending'
        latest_bill.save()

        # Provide a success message
        messages.success(request, "✅ Receipt uploaded successfully.")

    return render(request, 'core/ewallet_payment.html', {'bill': latest_bill})



@login_required
def settings_view(request):
    if request.user.is_superuser:
        return redirect('admin_settings')
       
    profile = Profile.objects.get(user=request.user)
    return render(request, 'core/settings.html',  {
        'user': request.user,
        'profile': profile
    })


def custom_logout(request):
    logout(request)
    return redirect('/accounts/login')