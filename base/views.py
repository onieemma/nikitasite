
from django.shortcuts import render, redirect,  get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings


from .models import Property, ContactInquiry, Contact

from django.template.loader import render_to_string



#PROPERTIES START

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from .models import Sector, Property, PropertyInquiry
import json


def properties_list(request):
    """
    Display all properties grouped by sector
    """
    sectors = Sector.objects.prefetch_related('properties').all()
    
    # Build the properties dictionary similar to the JavaScript structure
    properties_data = {}
    for sector in sectors:
        active_properties = sector.properties.filter(is_active=True)
        if active_properties.exists():
            properties_data[sector.slug] = {
                'name': sector.name,
                'properties': active_properties
            }
    
    context = {
        'properties_data': properties_data,
    }
    
    return render(request, 'base/properties.html', context)


@require_http_methods(["POST"])
def submit_property_inquiry(request):
    """
    Handle AJAX form submission for property inquiries
    """
    try:
        # Get form data
        property_id = request.POST.get('property_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        # Validate required fields
        if not all([property_id, full_name, email, phone, message]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)
        
        # Get the property
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Create inquiry
        inquiry = PropertyInquiry.objects.create(
            property=property_obj,
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            message=message,
            ip_address=ip_address
        )
        
        # Send email notification to admin
        try:
            admin_subject = f'New Property Inquiry: {property_obj.title}'
            admin_message = f"""
New property inquiry received:

Property: {property_obj.title}
Sector: {property_obj.sector.name}
Location: {property_obj.location}

Contact Information:
Name: {full_name}
Email: {email}
Phone: {phone}

Message:
{message}

Submitted at: {inquiry.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],  # Make sure to set this in settings.py
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending email: {e}")
        
        # Send confirmation email to user
        try:
            user_subject = f'Thank you for your inquiry about {property_obj.title}'
            user_message = f"""
Dear {full_name},

Thank you for your interest in {property_obj.title} located in {property_obj.location}.

We have received your inquiry and will get back to you as soon as possible.

Your inquiry details:
{message}

Best regards,
Nikitastite Real Estate Team
            """
            
            send_mail(
                user_subject,
                user_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending confirmation email: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your inquiry has been sent successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        }, status=500)
#PROPERTIES END


#EMAIL START

def get_client_ip(request):
    """Get client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def contact_inquiry_submit(request):
    """
    Handle the contact inquiry form submission from any page
    This is a POST-only view that redirects back to the referring page
    """
    if request.method == 'POST':
        # Get the checkboxes manually
        selling = request.POST.get('selling') == 'on'
        renting = request.POST.get('renting') == 'on'
        buying = request.POST.get('buying') == 'on'
        consent = request.POST.get('consent') == 'on'
        
        # Get other form fields
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not name or not email or not message:
            messages.error(request, 'Please fill in all required fields.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        if not consent:
            messages.error(request, 'You must agree to the Privacy Policy to submit.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Collect selected services
        services = []
        if selling:
            services.append('selling')
        if renting:
            services.append('renting')
        if buying:
            services.append('buying')
        
        # Create the inquiry
        try:
            inquiry = ContactInquiry.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                message=message,
                services_interested=', '.join(services) if services else None,
                consent_given=consent,
                ip_address=get_client_ip(request)
            )
            
            # Send emails
            try:
                send_inquiry_emails(inquiry)
            except Exception as e:
                print(f"Email sending failed: {str(e)}")
            
            messages.success(
                request, 
                'Thank you for contacting us! We have received your message and will get back to you soon.'
            )
        
        except Exception as e:
            messages.error(
                request,
                'There was an error submitting your message. Please try again.'
            )
            print(f"Form submission error: {str(e)}")
        
        # Redirect back to the page they came from
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # If not POST, redirect to home
    return redirect('/')


def send_inquiry_emails(inquiry):
    """
    Send email notifications for contact inquiry
    - One to admin/staff
    - One confirmation to user
    """
    
    # Email to Admin/Staff
    admin_subject = f'New Contact Inquiry from {inquiry.name}'
    admin_message = f"""
New Contact Inquiry Received

Name: {inquiry.name}
Email: {inquiry.email}
Services Interested In: {inquiry.get_services_display()}

Message:
{inquiry.message}

Submitted at: {inquiry.submitted_at.strftime('%B %d, %Y at %I:%M %p')}

---
This is an automated message from Nikita Global Realty contact form.
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

We have received your inquiry regarding: {inquiry.get_services_display()}

Our team will review your message and get back to you within 24-48 hours.

Your Message:
{inquiry.message}

If you have any urgent questions, please feel free to call us directly.

Best regards,
Nikita Global Realty Team

---
This is an automated confirmation email.
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
        print(f"Failed to send user confirmation email: {str(e)}")

#EMAIL END


#AUTH START
@csrf_protect
def signup_view(request):
    """Handle both GET (display form) and POST (process signup) requests"""
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('fullName', '').strip()
        email = request.POST.get('signupEmail', '').strip()
        password = request.POST.get('signupPassword', '')
        confirm_password = request.POST.get('confirmPassword', '')
        agree_terms = request.POST.get('agreeTerms')
        
        # Validation
        if not all([full_name, email, password, confirm_password]):
            messages.error(request, 'Please fill in all fields')
            return render(request, 'base/signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'base/signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'base/signup.html')
        
        if not agree_terms:
            messages.error(request, 'Please agree to the Terms and Conditions')
            return render(request, 'base/signup.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists')
            return render(request, 'base/signup.html')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists')
            return render(request, 'base/signup.html')
        
        try:
            # Split full name into first and last name
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Create user (using email as username)
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
    
    # GET request - display the form
    return render(request, 'base/signup.html')


@csrf_protect
def login_view(request):
    """Handle both GET (display form) and POST (process login) requests"""
    if request.method == 'POST':
        email = request.POST.get('loginEmail', '').strip()
        password = request.POST.get('loginPassword', '')
        remember_me = request.POST.get('rememberMe')
        
        # Validation
        if not email or not password:
            messages.error(request, 'Please fill in all fields')
            return render(request, 'base/signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'base/signup.html')
        
        # Authenticate user (using email as username)
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            
            # Handle "Remember Me"
            if not remember_me:
                # Session expires when browser closes
                request.session.set_expiry(0)
            else:
                # Session lasts for 2 weeks
                request.session.set_expiry(1209600)  # 2 weeks in seconds
            
            messages.success(request, 'Login successful! Redirecting...')
            return redirect('index')  # Redirects to index.html
        else:
            messages.error(request, 'Invalid email or password')
            return render(request, 'base/signup.html')
    
    # GET request - display the form
    return render(request, 'base/signup.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')

from .services.news_service import fetch_news_and_events


# HOME VIEW START


def home_view(request):
    articles = fetch_news_and_events(symbols="AAPL", limit=5)

    large_news = articles[0] if articles else None
    small_news = articles[1:3] if len(articles) > 1 else []

    context = {
        "large_news": large_news,
        "small_news": small_news,
    }
    return render(request, "base/index.html", context)



#HOME VIEW END

@require_http_methods(["POST"])
def contact_form_view(request):
    """Handle contact form submission via AJAX"""
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        comments = request.POST.get('comments', '').strip()
        human = request.POST.get('human')
        
        # Validation
        if not all([name, email, human]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields and confirm you are human.'
            }, status=400)
        
        # Save to database
        contact = Contact.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            email=email,
            phone=phone,
            comments=comments
        )
        
        # Send email notification
        try:
            subject = f'New Contact Form Submission from {name}'
            message = f"""
New contact form submission received:

Name: {name}
Email: {email}
Phone: {phone}

Message:
{comments}

Submitted at: {contact.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
User Account: {'Yes - ' + request.user.email if request.user.is_authenticated else 'No (Guest)'}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            # Log email error but don't fail the submission
            print(f"Email sending failed: {str(e)}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your message has been received.',
            'submitted_at': contact.submitted_at.strftime('%B %d, %Y at %I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
    










# ... your existing contact_form_view ...

@require_http_methods(["POST"])
def appointment_form_view(request):
    """Handle appointment form submission via AJAX"""
    try:
        # Get form data
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
        
        # Validate date format
        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time, '%H:%M').time()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid date or time format.'
            }, status=400)
        
        # Check if date is in the past
        from datetime import date as date_today
        if appointment_date < date_today.today():
            return JsonResponse({
                'success': False,
                'message': 'Please select a future date for your appointment.'
            }, status=400)
        
        # Map appointment type to database value
        type_mapping = {
            'Home Selling Consultation': 'home_selling',
            'Home Buying Consultation': 'home_buying',
            'Property Viewing': 'property_viewing',
            'General Inquiry': 'general_inquiry',
        }
        db_appointment_type = type_mapping.get(appointment_type, 'general_inquiry')
        
        # Save to database
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
        
        # Send email notification
        try:
            subject = f'New Appointment Request - {full_name}'
            email_message = f"""
New appointment request received:

CLIENT INFORMATION:
Name: {full_name}
Email: {email}
Phone: {phone}

APPOINTMENT DETAILS:
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {appointment_time.strftime('%I:%M %p')}
Type: {appointment_type}

MESSAGE:
{message if message else 'No additional message'}

BOOKING INFO:
Submitted at: {appointment.created_at.strftime('%Y-%m-%d %H:%M:%S')}
User Account: {'Yes - ' + request.user.email if request.user.is_authenticated else 'No (Guest)'}
Status: Pending Confirmation

---
Please confirm or reschedule this appointment as soon as possible.
            """
            
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            
            # Optional: Send confirmation email to client
            client_subject = f'Appointment Request Received - Nikita Global Realty'
            client_message = f"""
Dear {full_name},

Thank you for booking an appointment with Nikita Global Realty!

APPOINTMENT DETAILS:
Date: {appointment_date.strftime('%B %d, %Y')}
Time: {appointment_time.strftime('%I:%M %p')}
Type: {appointment_type}

We have received your appointment request and will confirm it shortly. You will receive a confirmation email once your appointment is confirmed.

If you need to make any changes, please contact us at:
Phone: +1 832 962 2241
Email: info@nikitaglobalrealty.com

Best regards,
Nikita Global Realty Team
            """
            
            send_mail(
                subject=client_subject,
                message=client_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,  # Don't fail if client email fails
            )
            
        except Exception as e:
            # Log email error but don't fail the submission
            print(f"Email sending failed: {str(e)}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'Your appointment has been submitted successfully! We will contact you shortly to confirm.',
            'appointment_date': appointment_date.strftime('%B %d, %Y'),
            'appointment_time': appointment_time.strftime('%I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)



def about_view(request):
    context = {}
    return render(request, "base/about.html", context)


def buywithus_view(request):
    context = {}
    return render(request, "base/buywithus.html", context)


def forsale_view(request):
    context = {}
    return render(request, "base/forsale.html", context)


def home_buy_view(request):
    context = {}
    return render(request, "base/home-buying.html", context)


def home_sell_view(request):
    context = {}
    return render(request, "base/home-selling.html", context)

def nikita_homes_view(request):
    context = {}
    return render(request, "base/nikitahomes.html", context)

def rental_view(request):
    context = {}
    return render(request, "base/rental.html", context)

def terms_view(request):
    context = {}
    return render(request, "base/terms.html", context)


def market_view(request):
    context = {}
    return render(request, "base/marketreport.html", context)



    #AI ASSIANT
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import google.generativeai as genai

# Configure Gemini using your API key from settings
genai.configure(api_key=settings.GEMINI_API_KEY)

@csrf_exempt
@require_http_methods(["POST"])
def chat_assistant(request):
    try:
        data = json.loads(request.body)
        messages = data.get('messages', [])
        user_message = messages[-1]['content'] if messages else ''

        # Use supported free-tier model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # System context for your assistant
        context = """You are a helpful real estate assistant for Nikita Global Realty. 
        We operate in USA (Texas/Houston), Nigeria (Lagos), and Ghana (Accra).
        Our CEO is Oyenike 'Nikki' Oyelakin, a top Realtor with Coldwell Banker.
        We help with buying, selling, and renting properties.
        Office: 16010 Barkers Point Lane, #555 Houston TX 77079.
        Be concise, friendly, and helpful."""

        # Generate AI response
        response = model.generate_content(f"{context}\n\nUser: {user_message}")

        return JsonResponse({
            'content': [{'type': 'text', 'text': response.text}]
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
