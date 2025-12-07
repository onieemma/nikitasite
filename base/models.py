

from django.db import models
from django.contrib.auth.models import User


#ESTATE NEWS START

from django.db import models

class NewsArticle(models.Model):
    source = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=1000)
    url = models.URLField(unique=True)
    published_at = models.DateTimeField(null=True, blank=True)
    raw_content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return f"{self.title} — {self.source}"



#ESTATE NEWS END

#POP UP CONTACT
class Contact(models.Model):
    # User info (if logged in)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Form fields
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)   # <--- NEW FIELD
    comments = models.TextField(blank=True, null=True)
    
    # Tracking
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
    
    def __str__(self):
        return f"{self.name} - {self.email} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    





# NEW APPOINTMENT MODEL
class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('home_selling', 'Home Selling Consultation'),
        ('home_buying', 'Home Buying Consultation'),
        ('property_viewing', 'Property Viewing'),
        ('general_inquiry', 'General Inquiry'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # User info (if logged in)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Form fields
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Appointment details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=50, choices=APPOINTMENT_TYPES)
    message = models.TextField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
    
    def __str__(self):
        return f"{self.full_name} - {self.appointment_date} at {self.appointment_time} ({self.get_status_display()})"
    




class ContactInquiry(models.Model):
    """
    Main contact form for general inquiries with service type selection
    """
    SERVICE_CHOICES = [
        ('selling', 'Selling'),
        ('renting', 'Renting'),
        ('buying', 'Buying'),
    ]
    
    # User info (if logged in)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Form fields
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField(help_text="How can we help?")
    
    # Service interests (stored as comma-separated values)
    services_interested = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Comma-separated: selling, renting, buying"
    )
    
    # Consent tracking
    consent_given = models.BooleanField(default=False)
    
    # Tracking
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'
    
    def __str__(self):
        return f"{self.name} - {self.email} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_services_list(self):
        """Returns list of services user is interested in"""
        if self.services_interested:
            return [s.strip() for s in self.services_interested.split(',')]
        return []
    
    def get_services_display(self):
        """Returns formatted display of services"""
        services = self.get_services_list()
        return ', '.join([s.capitalize() for s in services]) if services else 'None selected'



from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class Sector(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Property(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('recent', 'Recent'),
        ('trendy', 'Trendy'),
    ]
    
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='properties/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    
    # Optional: Add ordering and timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return self.title
    
    def get_formatted_price(self):
        """Returns price formatted with K or M suffix"""
        price = float(self.price)
        if price >= 1000000:
            return f"${price / 1000000:.1f}M"
        elif price >= 1000:
            return f"${price / 1000:.0f}K"
        else:
            return f"${price:.0f}"


class PropertyInquiry(models.Model):
    """
    Store inquiries about specific properties from the modal form
    """
    # Link to property
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    
    # User info (if logged in)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Form fields
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    
    # Tracking
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Property Inquiry'
        verbose_name_plural = 'Property Inquiries'
    
    def __str__(self):
        return f"{self.full_name} - {self.property.title} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"        
    


    from django.db import models

class FinancingInquiry(models.Model):
    property_price = models.DecimalField(max_digits=12, decimal_places=2)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    loan_term = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.monthly_payment:.2f} / {self.loan_term} yrs"


#BOOK
from django.db import models

class WealthBook(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)  # Optional: API or manual cover
    download_link = models.URLField(blank=True)  # EPUB / text link if allowed
    preview_link = models.URLField(blank=True)   # Optional Google/Open Library preview
    is_active = models.BooleanField(default=True)  # Show/hide book
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
