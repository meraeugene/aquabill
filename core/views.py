from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout,authenticate, login
from django.contrib import messages
from datetime import datetime, timedelta
from allauth.account.models import EmailAddress 
from core.forms import CustomSignupForm  
from allauth.account.utils import send_email_confirmation
from .models import Profile, Bill
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import random
import json

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
            if email_address and email_address.verified:
                login(request, user)
                return redirect('dashboard')
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
    total_bill = round(random.uniform(50.00, 300.00), 2)
    due_date = datetime.now() + timedelta(days=random.randint(5, 30))

    monthly_usage = {
        'January': random.randint(100, 300),
        'February': random.randint(100, 300),
        'March': random.randint(100, 300),
        'April': random.randint(100, 300),
        'May': random.randint(100, 300),
        'June': random.randint(100, 300),
        'July': random.randint(100, 300),
        'August': random.randint(100, 300),
        'September': random.randint(100, 300),
        'October': random.randint(100, 300),
        'November': random.randint(100, 300),
        'December': random.randint(100, 300),
    }

    request.session['total_bill'] = total_bill
    request.session['due_date'] = due_date.strftime("%Y-%m-%d")
    request.session['monthly_usage'] = monthly_usage 

    context = {
        'total_bill': total_bill,
        'due_date': due_date,
        'usage_labels': list(monthly_usage.keys()),
        'usage_values': list(monthly_usage.values()),
    }

    context['usage_labels_json'] = json.dumps(context['usage_labels'])
    context['usage_values_json'] = json.dumps(context['usage_values'])

    return render(request, 'core/dashboard.html', context)


@login_required
def bills(request):
    user_bills = Bill.objects.filter(user=request.user).order_by('due_date')
    return render(request, 'core/bills.html', {
        'bills': user_bills
    })


@login_required
def usage(request):
    monthly_usage = request.session.get('monthly_usage')

    if not monthly_usage:
        return redirect('dashboard')  

    total_consumption = sum(monthly_usage.values())
    average_daily_usage = round(total_consumption / 365, 2)
    average_monthly_usage = round(total_consumption / 12, 2)

    context = {
        'total_consumption': total_consumption,
        'average_daily_usage': average_daily_usage,
        'average_monthly_usage': average_monthly_usage,
        'usage_data': monthly_usage,
        'usage_labels_json': json.dumps(list(monthly_usage.keys())),
        'usage_values_json': json.dumps(list(monthly_usage.values())),
    }

    return render(request, 'core/usage.html', context)


@login_required
def payments(request):
    total_bill = request.session.get('total_bill')
    due_date = request.session.get('due_date')

    if not total_bill or not due_date:
        return redirect('dashboard')

    context = {
        'total_bill': total_bill,
        'due_date': due_date,
    }

    return render(request, 'core/payments.html', context)

@login_required
def payment_method_selection(request):
    total_bill = request.session.get('total_bill')
    due_date = request.session.get('due_date')

    if not total_bill or not due_date:
        return redirect('dashboard')


    context = {
        'total_bill': total_bill,
        'due_date': due_date,
    }

    return render(request, 'core/payment_method_selection.html', context)



@login_required
def payment_success(request):
    total_bill = request.session.get('total_bill')
    due_date = request.session.get('due_date')

    if not total_bill or not due_date:
        return redirect('dashboard')

    # Save to DB
    Bill.objects.create(
        user=request.user,
        period=datetime.now().strftime("%B %Y"),
        amount=total_bill,
        status='paid',
        due_date=due_date
    )

    return render(request, 'core/payment_success.html', {
        'total_bill': total_bill
    })

def download_receipt(request):
    total_bill = request.session.get('total_bill')
    due_date = request.session.get('due_date')

    if not total_bill or not due_date:
        return redirect('dashboard')

    template_path = 'core/receipt_template.html'
    context = {
        'user': request.user,
        'total_bill': total_bill,
        'due_date': due_date
    }

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="receipt.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF receipt')
    return response

@login_required
def email_receipt(request):
    total_bill = request.session.get('total_bill')
    due_date = request.session.get('due_date')

    if not total_bill or not due_date:
        return redirect('dashboard')

    subject = 'Your Aquabill Payment Receipt'
    message = render_to_string('core/receipt_template.html', {
        'user': request.user,
        'total_bill': total_bill,
        'due_date': due_date
    })

    email = EmailMessage(subject, message, to=[request.user.email])
    email.content_subtype = 'html'
    email.send()

    messages.success(request, "✅ Receipt emailed successfully.")
    return redirect('payment_success')

@login_required
def settings_view(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'core/settings.html',  {
        'user': request.user,
        'profile': profile
    })


def custom_logout(request):
    logout(request)
    return redirect('/accounts/login')