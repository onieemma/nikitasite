# from django.urls import path

from django.urls import path
from base.views import news_list_view
from . import views
from django.contrib.auth import views as auth_views
from .views import wealth_books_view


from django.shortcuts import redirect


def google_only_login(request):
    return redirect('google_login')

# app_name = 'base'

urlpatterns = [
    
      #GOOGLE


    path('accounts/login/', google_only_login),

    path('', views.home_view, name='index'),



     # Mortgage Calculator URLs
    path('mortgage-calculator/', views.mortgage_calculator_view, name='mortgage_calculator'),
    path('mortgage-calculate/', views.calculate_mortgage_ajax, name='calculate_mortgage'),
    path('submit-financing-inquiry/', views.submit_financing_inquiry, name='submit_inquiry'),


    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='base/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='base/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='base/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='base/password_reset_complete.html'), name='password_reset_complete'),

    

    # Contact
    path('contact/submit/', views.contact_form_view, name='contact_submit'),
    path('appointment/submit/', views.appointment_form_view, name='appointment_submit'),
    path('contact/submitting/', views.contact_inquiry_submit, name='contact_inquiry'),

    # Pages
    path('about/', views.about_view, name='about'),
    path('buywithus/', views.buywithus_view, name='buywithus'),
    path('forsale/', views.forsale_view, name='forsale'),
    path('homebuying/', views.home_buy_view, name='home_buy'),
    path('homesell/', views.home_sell_view, name='homesell'),
    path('nikita_home/', views.nikita_homes_view, name='nikita_home'),
    path('rental/', views.rental_view, name='rental'),
    path('terms/', views.terms_view, name='terms'),

    path("market/", views.market_view, name="market"),

    # API
    path('api/chat/', views.chat_assistant, name='chat_assistant'),

    path('properties/', views.properties_list, name='properties_list'),
    path('properties/inquiry/submit/', views.submit_property_inquiry, name='submit_property_inquiry'),

    # homebuying search 
      path("search/", views.property_search, name="property_search"),

      # home financing
      path('financing/', views.home_financing, name='home_financing'),

      # Books  
    path('wealth-books/', wealth_books_view, name='wealth_books'),

    #SITEMAP
     path('sitemap/', views.sitemap_view, name='sitemap'),


    path('quinnes-mortgage/', views.quinnes_mortgage, name='quinnes_mortgage'),
    path('quinnes/contact/submit/', views.quinnes_contact_submit, name='quinnes_contact_submit'),




  #NEWS
   path('news/', news_list_view, name='news_list'),
     

]
