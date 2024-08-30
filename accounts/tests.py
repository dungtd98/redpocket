from django.test import TestCase

# Create your tests here.
# tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from wallet.models import Wallet
from datetime import datetime


class CustomUserTests(TestCase):

    def setUp(self):
        self.user_model = get_user_model()

    def test_create_user(self):
        user = self.user_model.objects.create_user(username='testuser', password='testpass123')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertIsNone(user.telegram_id)
        self.assertEqual(user.daily_limit_open_pouch, 1)
        self.assertEqual(user.daily_limit_share_pouch, 1)

    def test_create_superuser(self):
        superuser = self.user_model.objects.create_superuser(username='admin', password='adminpass123')
        self.assertEqual(superuser.username, 'admin')
        self.assertTrue(superuser.check_password('adminpass123'))
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_referral_code_generation(self):
        user = self.user_model.objects.create_user(username='testuser2', password='testpass123')
        self.assertIsNotNone(user.referral_code)
        self.assertEqual(len(user.referral_code), 8)

    def test_user_str(self):
        user = self.user_model.objects.create_user(username='testuser3', password='testpass123')
        self.assertEqual(str(user), 'testuser3')


from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch
from wallet.models import Wallet
from datetime import datetime

User = get_user_model()

class GetUserProfileViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'password': 'testpassword',
                'telegram_id': '123456789',
                'first_name': 'Test',
                'last_name': 'User',
                'referral_code': 'testreferral',
                'claim_expire': datetime.now()
            }
        )
        
        # Check if the wallet already exists for the user
        self.wallet, created = Wallet.objects.get_or_create(
            user=self.user,
            defaults={
                'sniff_point': 100,
                'sniff_coin': 50
            }
        )
        
        self.client.force_authenticate(user=self.user)

    @patch('accounts.views.count_open_pouch', return_value=5)
    @patch('accounts.views.count_share_pouch', return_value=3)
    def test_get_user_profile(self, mock_count_share_pouch, mock_count_open_pouch):
        url = reverse('get_user_profile')  # Ensure this matches your URL name
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['data']['id'], self.user.id)
        self.assertEqual(response.data['data']['username'], self.user.username)
        self.assertEqual(response.data['data']['balance_sniff_point'], self.wallet.sniff_point)
        self.assertEqual(response.data['data']['balance_sniff_coin'], self.wallet.sniff_coin)
        self.assertEqual(response.data['data']['createdCountPouchToday'], 3)
        self.assertEqual(response.data['data']['openedCountPouchToday'], 5)