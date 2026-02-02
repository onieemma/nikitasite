from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator






from django.core.mail import send_mail
from django.http import HttpResponse






# base/views.py
# Add these imports and views to your existing views.py file

import os
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Get Census API key from environment variables
CENSUS_API_KEY = os.environ.get('CENSUS_API_KEY')

# ============================================
# LOCAL INFO API ENDPOINTS
# ============================================

@require_http_methods(["GET"])
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def census_data_api(request):
    """
    Fetch Census Bureau data for a Texas city
    GET /api/local-info/census/?city=Austin
    """
    try:
        city = request.GET.get('city', '').strip()
        
        if not city or len(city) < 2:
            return JsonResponse({'error': 'Invalid city name'}, status=400)
        
        state_fips = '48'  # Texas
        
        # Step 1: Get place code
        place_url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME&for=place:*&in=state:{state_fips}&key={CENSUS_API_KEY}"
        
        place_response = requests.get(place_url, timeout=10)
        place_response.raise_for_status()
        place_data = place_response.json()
        
        # Find matching city
        place_code = None
        search_city = city.lower()
        
        for i in range(1, len(place_data)):
            place_name = place_data[i][0].lower()
            if search_city in place_name:
                place_code = place_data[i][2]
                break
        
        if not place_code:
            return JsonResponse({'error': 'City not found in Census database'}, status=404)
        
        # Step 2: Get demographic data
        variables = [
            'NAME',
            'B01003_001E',  # Population
            'B19013_001E',  # Income
            'B15003_022E',  # Bachelor's
            'B15003_023E',  # Master's
            'B15003_024E',  # Professional
            'B15003_025E',  # Doctorate
            'B25077_001E',  # Home Value
            'B01002_001E',  # Age
            'B15003_001E'   # Total Ed
        ]
        
        data_url = f"https://api.census.gov/data/2022/acs/acs5?get={','.join(variables)}&for=place:{place_code}&in=state:{state_fips}&key={CENSUS_API_KEY}"
        
        data_response = requests.get(data_url, timeout=10)
        data_response.raise_for_status()
        census_data = data_response.json()
        
        if len(census_data) > 1:
            data = census_data[1]
            result = {
                'name': data[0],
                'population': data[1],
                'medianIncome': data[2],
                'bachelors': data[3],
                'masters': data[4],
                'professional': data[5],
                'doctorate': data[6],
                'medianHomeValue': data[7],
                'medianAge': data[8],
                'totalEducation': data[9]
            }
            
            return JsonResponse({
                'data': result,
                'source': 'US Census Bureau - ACS 5-Year 2022'
            })
        else:
            return JsonResponse({'error': 'No Census data available'}, status=404)
            
    except requests.exceptions.Timeout:
        logger.error('Census API timeout')
        return JsonResponse({'error': 'Census API request timeout'}, status=504)
    except requests.exceptions.RequestException as e:
        logger.error(f'Census API error: {str(e)}')
        return JsonResponse({'error': 'Failed to fetch Census data'}, status=500)
    except Exception as e:
        logger.error(f'Unexpected error in census_data_api: {str(e)}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
@cache_page(60 * 60 * 24 * 7)  # Cache for 7 days
def geocode_api(request):
    """
    Geocode a location using OpenStreetMap Nominatim
    GET /api/local-info/geocode/?q=Austin, Texas, USA
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({'error': 'Invalid search query'}, status=400)
        
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1&addressdetails=1"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'DjangoTexasLocalInfo/1.0'
        })
        response.raise_for_status()
        
        data = response.json()
        
        return JsonResponse({
            'data': data,
            'source': 'OpenStreetMap Nominatim'
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Geocoding service timeout'}, status=504)
    except requests.exceptions.RequestException as e:
        logger.error(f'Geocoding error: {str(e)}')
        return JsonResponse({'error': 'Geocoding service unavailable'}, status=500)
    except Exception as e:
        logger.error(f'Unexpected error in geocode_api: {str(e)}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
@cache_page(60 * 60 * 24 * 7)  # Cache for 7 days
def schools_api(request):
    """
    Get schools data from OpenStreetMap Overpass API
    GET /api/local-info/schools/?lat=30.2672&lon=-97.7431
    """
    try:
        lat = request.GET.get('lat', '')
        lon = request.GET.get('lon', '')
        
        try:
            latitude = float(lat)
            longitude = float(lon)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return JsonResponse({'error': 'Coordinates out of range'}, status=400)
        
        radius = 5000  # 5km
        query = f"""
            [out:json][timeout:25];
            (
                node["amenity"="school"](around:{radius},{latitude},{longitude});
                way["amenity"="school"](around:{radius},{latitude},{longitude});
                relation["amenity"="school"](around:{radius},{latitude},{longitude});
            );
            out body;
            >;
            out skel qt;
        """
        
        response = requests.post(
            'https://overpass-api.de/api/interpreter',
            data={'data': query},
            timeout=30,
            headers={'User-Agent': 'DjangoTexasLocalInfo/1.0'}
        )
        response.raise_for_status()
        
        data = response.json()
        schools = data.get('elements', [])
        
        return JsonResponse({
            'data': schools,
            'count': len(schools),
            'source': 'OpenStreetMap Overpass API'
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Schools API timeout'}, status=504)
    except requests.exceptions.RequestException as e:
        logger.error(f'Schools API error: {str(e)}')
        return JsonResponse({'error': 'Schools data unavailable'}, status=500)
    except Exception as e:
        logger.error(f'Unexpected error in schools_api: {str(e)}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
@cache_page(60 * 30)  # Cache for 30 minutes
def weather_api(request):
    """
    Get weather data from Open-Meteo API
    GET /api/local-info/weather/?lat=30.2672&lon=-97.7431
    """
    try:
        lat = request.GET.get('lat', '')
        lon = request.GET.get('lon', '')
        
        try:
            latitude = float(lat)
            longitude = float(lon)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return JsonResponse({'error': 'Coordinates out of range'}, status=400)
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&timezone=America/Chicago"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'DjangoTexasLocalInfo/1.0'
        })
        response.raise_for_status()
        
        data = response.json()
        
        return JsonResponse({
            'data': data,
            'source': 'Open-Meteo API'
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Weather API timeout'}, status=504)
    except requests.exceptions.RequestException as e:
        logger.error(f'Weather API error: {str(e)}')
        return JsonResponse({'error': 'Weather service unavailable'}, status=500)
    except Exception as e:
        logger.error(f'Unexpected error in weather_api: {str(e)}')
        return JsonResponse({'error': 'Internal server error'}, status=500)


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@require_http_methods(["GET"])
def api_health_check(request):
    """
    Health check endpoint to verify API is working
    GET /api/local-info/health/
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'Texas Local Info API',
        'endpoints': {
            'census': '/api/local-info/census/?city=Austin',
            'geocode': '/api/local-info/geocode/?q=Austin, Texas',
            'schools': '/api/local-info/schools/?lat=30.2672&lon=-97.7431',
            'weather': '/api/local-info/weather/?lat=30.2672&lon=-97.7431'
        }
    })







def test_email(request):
    try:
        send_mail(
            subject='Render SMTP Test',
            message='Testing Zoho SMTP from Render',
            from_email='info@nikitaglobalrealty.com',  # CHANGE IF DIFFERENT
            recipient_list=['info@nikitaglobalrealty.com'],  # or your personal email
            fail_silently=False,
        )
        return HttpResponse("Email sent successfully")
    except Exception as e:
        return HttpResponse(f"Error: {e}")



# ============================================================================
# QUINNES MORTGAGE - Add to existing views.py
# ============================================================================

def quinnes_mortgage(request):
    """Main view for Quinnes Mortgage page"""
    context = {
        'page_title': 'Quinnes Mortgage',
        'tagline': 'Your Trusted Partner in Home Financing Solutions'
    }
    return render(request, 'base/quinnes_mortgage.html', context)


@require_http_methods(["POST"])
def quinnes_contact_submit(request):
    """Handle Quinnes Mortgage contact form submission (separate from main contact)"""
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        country = request.POST.get('country')
        comments = request.POST.get('comments')
        
        # Validate required fields
        if not name or not email or not country:
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            })
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            })
        
        # Save to your existing Contact model (reusing your infrastructure)
        contact = Contact.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            email=email,
            phone=phone,
            country=country,
            comments=f"[QUINNES MORTGAGE] {comments}"  # Tag it to identify source
        )
        
        # Send email notification using your existing email setup
        try:
            subject = f'New Quinnes Mortgage Inquiry from {name}'
            message = f"""
New Quinnes Mortgage Contact Form Submission:

Name: {name}
Email: {email}
Phone: {phone}
Country: {country}

Message:
{comments}

Submitted: {contact.submitted_at.strftime('%B %d, %Y at %I:%M %p')}
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for contacting Quinnes Mortgage! We will get back to you within 24 hours.',
            'submitted_at': contact.submitted_at.strftime('%B %d, %Y at %I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        })

# ============================================================================
# MORTGAGE CALCULATION - views.py
# ============================================================================
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json
from .forms import MortgageCalculatorForm, FinancingInquiryForm
from .models import FinancingInquiry


def calculate_monthly_payment(home_price, down_payment, interest_rate, loan_term):
    """
    Calculate monthly mortgage payment using the standard mortgage formula.
    
    M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1]
    
    Where:
    M = Monthly payment
    P = Principal loan amount
    i = Monthly interest rate
    n = Number of payments (months)
    """
    principal = Decimal(home_price) - Decimal(down_payment)
    
    if principal <= 0:
        return 0
    
    if interest_rate == 0:
        return principal / (loan_term * 12)
    
    monthly_rate = Decimal(interest_rate) / Decimal(100) / Decimal(12)
    num_payments = loan_term * 12
    
    # Calculate monthly payment
    monthly_payment = principal * (
        monthly_rate * (1 + monthly_rate) ** num_payments
    ) / (
        (1 + monthly_rate) ** num_payments - 1
    )
    
    return round(monthly_payment, 2)


def mortgage_calculator_view(request):
    """Main view for mortgage calculator page"""
    calculator_form = MortgageCalculatorForm()
    inquiry_form = FinancingInquiryForm()
    
    context = {
        'calculator_form': calculator_form,
        'inquiry_form': inquiry_form,
    }
    
    return render(request, 'base/mortgage_calculator.html', context)


@require_http_methods(["POST"])
def calculate_mortgage_ajax(request):
    """AJAX endpoint for calculating mortgage payment"""
    try:
        data = json.loads(request.body)
        
        home_price = Decimal(data.get('home_price', 0))
        down_payment = Decimal(data.get('down_payment', 0))
        interest_rate = Decimal(data.get('interest_rate', 0))
        loan_term = int(data.get('loan_term', 30))
        
        monthly_payment = calculate_monthly_payment(
            home_price, down_payment, interest_rate, loan_term
        )
        
        principal = home_price - down_payment
        total_interest = (monthly_payment * loan_term * 12) - principal
        total_payment = monthly_payment * loan_term * 12
        
        # Calculate property tax (estimated 1.2% annually)
        property_tax = (home_price * Decimal('0.012')) / Decimal(12)
        
        # Calculate home insurance (estimated 0.5% annually)
        home_insurance = (home_price * Decimal('0.005')) / Decimal(12)
        
        # Calculate PMI if down payment < 20%
        pmi = Decimal(0)
        down_payment_percent = (down_payment / home_price) * 100
        if down_payment_percent < 20:
            pmi = principal * Decimal('0.01') / Decimal(12)
        
        total_monthly = monthly_payment + property_tax + home_insurance + pmi
        
        return JsonResponse({
            'success': True,
            'monthly_payment': float(monthly_payment),
            'principal': float(principal),
            'total_interest': float(total_interest),
            'total_payment': float(total_payment),
            'property_tax': float(property_tax),
            'home_insurance': float(home_insurance),
            'pmi': float(pmi),
            'total_monthly': float(total_monthly),
            'down_payment_percent': float(down_payment_percent)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


#=================
#FINANCING INQUIRY
#================
@require_http_methods(["POST"])
def submit_financing_inquiry(request):
    """Handle financing inquiry form submission"""
    form = FinancingInquiryForm(request.POST)
    
    if form.is_valid():
        inquiry = form.save(commit=False)
        
        # Calculate and save monthly payment
        monthly_payment = calculate_monthly_payment(
            inquiry.home_price,
            inquiry.down_payment,
            inquiry.interest_rate,
            inquiry.loan_term
        )
        inquiry.monthly_payment = monthly_payment
        inquiry.save()
        
        messages.success(
            request, 
            'Your financing inquiry has been submitted successfully! '
            'We will contact you soon.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Inquiry submitted successfully',
            'inquiry_id': inquiry.id
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)

# ============================================================================
# MORTGAGE CALCULATOR- views.py
# ============================================================================

import json
import requests
from datetime import datetime

from .models import (
    Appointment, Property, Sector, ContactInquiry, 
    Contact, PropertyInquiry, NewsArticle, WealthBook,
    FinancingInquiry
)
from .forms import InvestmentInputForm

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_client_ip(request):
    """Get client's IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip




# ============================================================================
# ERROR HANDLERS
# ============================================================================

def custom_404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)


def custom_403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)


def custom_400(request, exception):
    """Custom 400 error handler"""
    return render(request, 'errors/400.html', status=400)


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

@csrf_protect
def signup_view(request):
    """Handle user signup"""
    if request.method == 'POST':
        full_name = request.POST.get('fullName', '').strip()
        email = request.POST.get('signupEmail', '').strip()
        password = request.POST.get('signupPassword', '')
        confirm_password = request.POST.get('confirmPassword', '')
        agree_terms = request.POST.get('agreeTerms')
        
        # Validation
        if not all([full_name, email, password, confirm_password]):
            messages.error(request, 'Please fill in all fields')
            return render(request, 'base/signup.html')
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'base/signup.html')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'base/signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'base/signup.html')
        
        if not agree_terms:
            messages.error(request, 'Please agree to the Terms and Conditions')
            return render(request, 'base/signup.html')
        
        # Check if user exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists')
            return render(request, 'base/signup.html')
        
        try:
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            messages.success(request, 'Account created successfully! Please sign in.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'base/signup.html')
    
    return render(request, 'base/signup.html')


@csrf_protect
def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        email = request.POST.get('loginEmail', '').strip()
        password = request.POST.get('loginPassword', '')
        remember_me = request.POST.get('rememberMe')
        
        if not email or not password:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'base/signup.html')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Handle "Remember Me"
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(request, 'Login successful!')
            
            # Redirect to next parameter or home
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password')
            return render(request, 'base/signup.html')
    
    return render(request, 'base/signup.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


# ============================================================================
# GOOGLE OAUTH
# ============================================================================




# ============================================================================
# HOME & PAGE VIEWS
# ============================================================================


def home_view(request):
    """Home page view with news and properties"""
    try:
        from .services.news_service import fetch_news_and_events
        articles = fetch_news_and_events(symbols="AAPL", limit=5)
    except Exception as e:
        print(f"News fetch error: {e}")
        articles = []
    
    large_news = articles[0] if articles else None
    small_news = articles[1:3] if len(articles) > 1 else []
    
    # Properties data
    sectors = Sector.objects.prefetch_related('properties').all()
    properties_data = {}
    for sector in sectors:
        active_properties = sector.properties.filter(is_active=True)[:5]  # Limit to 5
        if active_properties.exists():
            properties_data[sector.slug] = {
                'name': sector.name,
                'properties': active_properties
            }
    
    context = {
        "large_news": large_news,
        "small_news": small_news,
        "properties_data": properties_data,
    }
    return render(request, "base/index.html", context)


def about_view(request):
    return render(request, "base/about.html")


def buywithus_view(request):
    return render(request, "base/buywithus.html")


def forsale_view(request):
    return render(request, "base/forsale.html")


def home_buy_view(request):
    return render(request, "base/home_buying.html")


def sell_view(request):
    return render(request, "base/home_sell.html")


def home_market(request):
    return render(request, "base/home_resell.html")

def nikita_homes_view(request):
    return render(request, "base/nikitahomes.html")


def rental_view(request):
    return render(request, "base/rental.html")


def terms_view(request):
    return render(request, "base/terms.html")


def market_view(request):
    return render(request, "base/marketreport.html")


# ============================================================================
# CONTACT & FORMS
# ============================================================================

@require_http_methods(["POST"])
def contact_form_view(request):
    """Handle contact form submission via AJAX"""
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        country = request.POST.get('country', '').strip()
        comments = request.POST.get('comments', '').strip()
        human = request.POST.get('human')
        
        # Validation
        if not all([name, email, human]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            }, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)
        
        # Save to database
        contact = Contact.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            email=email,
            phone=phone,
            country=country,
            comments=comments
        )
        
        # Send email notification
        try:
            subject = f'New Contact Form Submission from {name}'
            message = f"""
New contact form submission:

Name: {name}
Email: {email}
Phone: {phone}
Country: {country}

Message:
{comments}

Submitted: {contact.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your message has been received.',
            'submitted_at': contact.submitted_at.strftime('%B %d, %Y at %I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


@require_http_methods(["POST"])
def appointment_form_view(request):
    """Handle appointment form submission"""
    try:
        full_name = request.POST.get('fullName', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        date = request.POST.get('date', '').strip()
        time = request.POST.get('time', '').strip()
        appointment_type = request.POST.get('type', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validation
        if not all([full_name, email, phone, date, time, appointment_type]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            }, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)
        
        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time, '%H:%M').time()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid date or time format.'
            }, status=400)
        
        # Check past date
        from datetime import date as date_today
        if appointment_date < date_today.today():
            return JsonResponse({
                'success': False,
                'message': 'Please select a future date.'
            }, status=400)
        
        # Map appointment type
        type_mapping = {
            'Home Selling Consultation': 'home_selling',
            'Home Buying Consultation': 'home_buying',
            'Property Viewing': 'property_viewing',
            'General Inquiry': 'general_inquiry',
        }
        db_appointment_type = type_mapping.get(appointment_type, 'general_inquiry')
        
        # Create appointment
        appointment = Appointment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            appointment_type=db_appointment_type,
            message=message
        )
        
        # Send emails
        try:
            subject = f'New Appointment Request - {full_name}'
            email_message = f"""
New appointment request:

Name: {full_name}
Email: {email}
Phone: {phone}
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {appointment_time.strftime('%I:%M %p')}
Type: {appointment_type}

Message: {message if message else 'None'}

Submitted: {appointment.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment submitted successfully! We will contact you shortly.',
            'appointment_date': appointment_date.strftime('%B %d, %Y'),
            'appointment_time': appointment_time.strftime('%I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)



# ============================================================================
# PROPERTIES
# ============================================================================

def properties_list(request):
    """Display properties grouped by sector"""
    sectors = Sector.objects.prefetch_related('properties').all()
    
    properties_data = {}
    for sector in sectors:
        active_properties = sector.properties.filter(is_active=True)
        if active_properties.exists():
            properties_data[sector.slug] = {
                'name': sector.name,
                'properties': active_properties
            }
    
    return render(request, 'base/properties.html', {
        'properties_data': properties_data
    })


def property_search(request):
    """Search properties"""
    query = request.GET.get("q", "").strip()
    
    if query:
        results = Property.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(sector__name__icontains=query) |
            Q(status__icontains=query)
        ).filter(is_active=True)[:20]  # Limit results
    else:
        results = Property.objects.none()
    
    return render(request, "base/search_results.html", {
        "query": query,
        "results": results
    })


@require_http_methods(["POST"])
def submit_property_inquiry(request):
    """Handle property inquiry form"""
    try:
        property_id = request.POST.get('property_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        if not all([property_id, full_name, email, phone, message]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)
        
        property_obj = get_object_or_404(Property, id=property_id)
        
        inquiry = PropertyInquiry.objects.create(
            property=property_obj,
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            message=message,
            ip_address=get_client_ip(request)
        )
        
        # Send notification
        try:
            subject = f'New Property Inquiry: {property_obj.title}'
            email_message = f"""
Property inquiry received:

Property: {property_obj.title}
Sector: {property_obj.sector.name}
Location: {property_obj.location}

Contact:
Name: {full_name}
Email: {email}
Phone: {phone}

Message: {message}

Submitted: {inquiry.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your inquiry has been sent.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


# ============================================================================
# HOME FINANCING
# ============================================================================

def home_financing(request):
    """Home financing calculator"""
    monthly_payment = None
    
    if request.method == 'GET' and request.GET:
        try:
            P = float(request.GET.get('property_price', 0))
            D = float(request.GET.get('down_payment', 0))
            r = float(request.GET.get('interest_rate', 0)) / 100 / 12
            n = int(request.GET.get('loan_term', 0)) * 12
            L = P - D
            
            if r > 0 and n > 0:
                monthly_payment = L * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
                monthly_payment = round(monthly_payment, 2)
        except (ValueError, ZeroDivisionError):
            monthly_payment = None
    
    return render(request, 'base/home_financing.html', {
        'monthly_payment': monthly_payment
    })



# ============================================================================
# NEWS VIEW (base/views.py)
# ============================================================================

from django.shortcuts import render
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .models import NewsArticle

@cache_page(60 * 15)  # Cache for 15 minutes
def news_list_view(request):
    """Display news articles with pagination and filtering"""
    
    # Get filter parameters
    source_filter = request.GET.get('source', '')
    
    # Base queryset
    articles_list = NewsArticle.objects.all()
    
    # Apply filters
    if source_filter:
        articles_list = articles_list.filter(source__icontains=source_filter)
    
    # Order by published date
    articles_list = articles_list.order_by('-published_at')
    
    # Get all sources for filter dropdown
    sources = NewsArticle.objects.values_list('source', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(articles_list, 20)  # 20 per page
    page_number = request.GET.get('page')
    articles = paginator.get_page(page_number)
    
    context = {
        'articles': articles,
        'sources': sources,
        'current_source': source_filter,
    }
    
    return render(request, 'base/news_list.html', context)


# ============================================================================
# BOOKS
# ============================================================================


def wealth_books_view(request):
    """Display wealth building books"""
    admin_books = WealthBook.objects.filter(is_active=True)
    
    try:
        from .services.gutendex_service import get_books_from_gutendex
        api_books = get_books_from_gutendex(subject="finance")
    except Exception as e:
        print(f"API error: {e}")
        api_books = []
    
    return render(request, 'base/wealth_books.html', {
        'admin_books': admin_books,
        'api_books': api_books,
    })


# ============================================================================
# SITEMAP
# ============================================================================

def sitemap_view(request):
    """Human-readable sitemap"""
    sectors = Sector.objects.all()
    properties = Property.objects.filter(is_active=True)[:50]  # Limit for performance
    
    return render(request, 'base/sitemap.html', {
        'sectors': sectors,
        'properties': properties,
    })


# ============================================================================
# AI CHAT ASSISTANT
# ============================================================================

@require_http_methods(["POST"])
def chat_assistant(request):
    """AI chat assistant using Google Gemini"""
    try:
        import google.generativeai as genai
        
        data = json.loads(request.body)
        messages = data.get('messages', [])
        user_message = messages[-1]['content'] if messages else ''
        
        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # System context
        context = """You are a helpful real estate assistant for Nikita Global Realty. 
We operate in USA (Texas/Houston), Nigeria (Lagos), and Ghana (Accra).
Our CEO is Oyenike 'Nikki' Oyelakin, a top Realtor with Coldwell Bank1er.
We help with buying, selling, and renting properties.
Office: 16010 Barkers Point Lane, #555 Houston TX 77079.
Be concise, friendly, and helpful."""
        
        # Generate response
        response = model.generate_content(f"{context}\n\nUser: {user_message}")
        
        return JsonResponse({
            'content': [{'type': 'text', 'text': response.text}]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




# def contact_inquiry_submit(request):
#     """Handle contact inquiry with service checkboxes"""
#     if request.method == 'POST':
#         selling = request.POST.get('selling') == 'on'
#         renting = request.POST.get('renting') == 'on'
#         buying = request.POST.get('buying') == 'on'
#         consent = request.POST.get('consent') == 'on'
        
#         name = request.POST.get('name', '').strip()
#         email = request.POST.get('email', '').strip()
#         message = request.POST.get('message', '').strip()
        
#         if not name or not email or not message:
#             messages.error(request, 'Please fill in all required fields.')
#             return redirect(request.META.get('HTTP_REFERER', '/'))
        
#         if not consent:
#             messages.error(request, 'You must agree to the Privacy Policy.')
#             return redirect(request.META.get('HTTP_REFERER', '/'))
        
#         services = []
#         if selling:
#             services.append('selling')
#         if renting:
#             services.append('renting')
#         if buying:
#             services.append('buying')
        
#         try:
#             inquiry = ContactInquiry.objects.create(
#                 user=request.user if request.user.is_authenticated else None,
#                 name=name,
#                 email=email,
#                 message=message,
#                 services_interested=', '.join(services) if services else None,
#                 consent_given=consent,
#                 ip_address=get_client_ip(request)
#             )
            
#             try:
#                 send_inquiry_emails(inquiry)
#             except Exception as e:
#                 print(f"Email error: {str(e)}")
            
#             messages.success(request, 'Thank you! We will get back to you soon.')
        
#         except Exception as e:
#             messages.error(request, 'An error occurred. Please try again.')
#             print(f"Form error: {str(e)}")
        
#         return redirect(request.META.get('HTTP_REFERER', '/'))
    
#     return redirect('/')





def contact_inquiry_submit(request):
    """Handle contact inquiry with service checkboxes"""
    if request.method == 'POST':
        # Get checkbox values
        selling = request.POST.get('selling') == 'on'
        renting = request.POST.get('renting') == 'on'
        buying = request.POST.get('buying') == 'on'
        consent = request.POST.get('consent') == 'on'
        
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not name or not email or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        if not consent:
            messages.error(request, 'You must agree to the Privacy Policy.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Build services list
        services = []
        if selling:
            services.append('Selling')
        if renting:
            services.append('Renting')
        if buying:
            services.append('Buying')
        
        # Join services or set default message
        services_text = ', '.join(services) if services else 'General Inquiry'
        
        try:
            inquiry = ContactInquiry.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                message=message,
                services_interested=services_text,
                consent_given=consent,
                ip_address=get_client_ip(request)
            )
            
            # Send emails
            try:
                send_inquiry_emails(inquiry)
            except Exception as e:
                print(f"Email error: {str(e)}")
            
            messages.success(request, 'Thank you! We will get back to you soon.')
        
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            print(f"Form error: {str(e)}")
        
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return redirect('/')


def send_inquiry_emails(inquiry):
    """Send email notifications for contact inquiry"""
    
    # Email to Admin
    admin_subject = f'New Contact Inquiry from {inquiry.name}'
    admin_message = f"""
New Contact Inquiry Received

Name: {inquiry.name}
Email: {inquiry.email}
Services Interested In: {inquiry.services_interested or 'General Inquiry'}

Message:
{inquiry.message}

Submitted at: {inquiry.submitted_at.strftime('%B %d, %Y at %I:%M %p')}
"""
    
    try:
        send_mail(
            subject=admin_subject,
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send admin email: {str(e)}")
    
    # Confirmation Email to User
    user_subject = 'Thank you for contacting Nikita Global Realty'
    user_message = f"""
Dear {inquiry.name},

Thank you for reaching out to Nikita Global Realty!

We have received your inquiry regarding: {inquiry.services_interested or 'your real estate needs'}

Our team will review your message and get back to you within 24-48 hours.

Best regards,
Nikita Global Realty Team

---
This is an automated message. Please do not reply to this email.
For urgent inquiries, call us at: (555) 123-4567
"""
    
    try:
        send_mail(
            subject=user_subject,
            message=user_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email],
            fail_silently=False,
        )
    except Exception as e:

        print(f"Failed to send confirmation email: {str(e)}")



