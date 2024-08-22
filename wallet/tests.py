from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Wallet, GiveawayPouch
from unittest.mock import patch
import json

User = get_user_model()

class CreateGiveawayPouchViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.wallet = Wallet.objects.create(user=self.user, sniff_coin=100)
        self.client.force_authenticate(user=self.user)
        self.url = 'http://localhost:8000/create-giveaway-pouch/'  # Update this with the actual URL

    @patch('wallet.views.can_open_pouch', return_value=True)
    @patch('wallet.views.divide_into_percentage_array', return_value=[10, 20, 30])
    @patch('wallet.views.save_to_redis')
    def test_create_giveaway_pouch_success(self, mock_save_to_redis, mock_divide_into_percentage_array, mock_can_open_pouch):
        data = {
            'sniff_coin': 10
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GiveawayPouch.objects.count(), 1)
        self.assertEqual(GiveawayPouch.objects.get().sniff_coin, 10)
        mock_save_to_redis.assert_called_once()

    @patch('wallet.views.can_open_pouch', return_value=False)
    def test_create_giveaway_pouch_daily_limit(self, mock_can_open_pouch):
        data = {
            'sniff_coin': 10
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You have reached the daily limit of opening pouch.', response.data['message'])

    @patch('wallet.views.can_open_pouch', return_value=True)
    def test_create_giveaway_pouch_invalid_data(self, mock_can_open_pouch):
        data = {
            'sniff_coin': 'invalid'  # Invalid data type
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A valid number is required.', response.data['sniff_coin'][0])