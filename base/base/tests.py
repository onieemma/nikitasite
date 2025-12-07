from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Lead


class LeadAuthTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_signup_creates_lead_and_user(self):
		data = {
			"full_name": "John Doe",
			"email": "johndoe@example.com",
			"password": "s3cur3pass"
		}
		response = self.client.post(reverse('signup-lead'), data)
		self.assertEqual(response.status_code, 200)
		json_data = response.json()
		self.assertTrue(json_data.get('success'))
		# User and Lead created
		self.assertTrue(Lead.objects.filter(email=data['email']).exists())
		self.assertTrue(User.objects.filter(username=data['email']).exists())

	def test_login_with_user_account(self):
		# Create a normal Django user and test login
		user = User.objects.create_user(username='testuser@example.com', email='testuser@example.com', password='pass1234')
		data = {"email_or_username": 'testuser@example.com', "password": 'pass1234'}
		response = self.client.post(reverse('login-lead'), data)
		self.assertEqual(response.status_code, 200)
		json_data = response.json()
		self.assertTrue(json_data.get('success'))
		# Session should contain user id
		self.assertIn('_auth_user_id', self.client.session)

	def test_login_with_lead_only_creates_user(self):
		# Create a Lead manually with hashed password
		from django.contrib.auth.hashers import make_password
		Lead.objects.create(full_name='Lead Only', email='leads@example.com', password=make_password('leadpass'), source='signup')
		data = {"email_or_username": 'leads@example.com', "password": 'leadpass'}
		response = self.client.post(reverse('login-lead'), data)
		self.assertEqual(response.status_code, 200)
		json_data = response.json()
		self.assertTrue(json_data.get('success'))
		# A Django User should now exist
		self.assertTrue(User.objects.filter(username='leads@example.com').exists())
