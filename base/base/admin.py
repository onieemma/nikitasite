from django.contrib import admin
from .models import Contact, Appointment, ContactInquiry, Sector, Property
1
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'submitted_at', 'responded']
    list_filter = ['responded', 'submitted_at']
    search_fields = ['name', 'email', 'phone', 'comments']
    readonly_fields = ['submitted_at', 'user']
    list_editable = ['responded']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'user')
        }),
        ('Message', {
            'fields': ('comments',)
        }),
        ('Tracking', {
            'fields': ('submitted_at', 'responded')
        }),
    )

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'appointment_date', 'appointment_time', 'appointment_type', 'status', 'created_at']
    list_filter = ['status', 'appointment_type', 'appointment_date', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'message']
    readonly_fields = ['created_at', 'updated_at', 'user']
    list_editable = ['status']
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Client Information', {
            'fields': ('full_name', 'email', 'phone', 'user')
        }),
        ('Appointment Details', {
            'fields': ('appointment_date', 'appointment_time', 'appointment_type', 'message')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    def get_list_display_links(self, request, list_display):
        return ['full_name']
    





from django.contrib import admin
from .models import Sector, Property, PropertyInquiry


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'property_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def property_count(self, obj):
        return obj.properties.count()
    property_count.short_description = 'Number of Properties'


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'sector', 'location', 'price', 'status', 'is_active', 'created_at')
    search_fields = ('title', 'location', 'description')
    list_filter = ('sector', 'status', 'is_active', 'created_at')
    list_editable = ('status', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sector', 'title', 'location', 'status')
        }),
        ('Pricing & Description', {
            'fields': ('price', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'property', 'submitted_at', 'responded')
    search_fields = ('full_name', 'email', 'phone', 'message')
    list_filter = ('responded', 'submitted_at', 'property__sector')
    readonly_fields = ('submitted_at', 'ip_address', 'user', 'property')
    list_editable = ('responded',)
    
    fieldsets = (
        ('Property Information', {
            'fields': ('property',)
        }),
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Inquiry Details', {
            'fields': ('message',)
        }),
        ('Tracking', {
            'fields': ('user', 'submitted_at', 'ip_address', 'responded'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent manual creation - inquiries come from the website
        return False




@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'email', 
        'get_services_display', 
        'submitted_at', 
        'responded',
        'consent_given'
    ]
    
    list_filter = [
        'responded', 
        'consent_given', 
        'submitted_at',
    ]
    
    search_fields = [
        'name', 
        'email', 
        'message', 
        'services_interested'
    ]
    
    readonly_fields = [
        'user', 
        'name', 
        'email', 
        'message', 
        'services_interested',
        'consent_given',
        'submitted_at',
        'ip_address',
        'get_services_display'
    ]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'user')
        }),
        ('Inquiry Details', {
            'fields': ('services_interested', 'get_services_display', 'message')
        }),
        ('Consent & Tracking', {
            'fields': ('consent_given', 'submitted_at', 'ip_address', 'responded')
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'submitted_at'
    
    # Make responded editable in list view
    list_editable = ['responded']
    
    def has_add_permission(self, request):
        # Disable manual adding through admin
        return False
    
    def get_services_display(self, obj):
        return obj.get_services_display()
    get_services_display.short_description = 'Services Interested'


 


from django.contrib import admin
from .models import WealthBook

@admin.register(WealthBook)
class WealthBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_active', 'created_at')
    search_fields = ('title', 'author')
    list_filter = ('is_active',)
