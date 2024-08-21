from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Wallet, GiveawayPouch
import json

User = get_user_model()

class CreateGiveawayPouchViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.wallet = Wallet.objects.create(user=self.user, sniff_coin=100)
        self.client.force_authenticate(user=self.user)
        self.url = '/path/to/create-giveaway-pouch/'  # Update this with the actual URL

    def test_create_giveaway_pouch_success(self):
        data = {
            'sniff_coin': 10
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GiveawayPouch.objects.count(), 1)
        self.assertEqual(GiveawayPouch.objects.get().sniff_coin, 10)

    def test_create_giveaway_pouch_exceeds_limit(self):
        data = {
            'sniff_coin': 30  # Exceeds 20% of wallet's sniff coin
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You can only allocate up to 20%', response.data['sniff_coin'][0])

    def test_create_giveaway_pouch_invalid_data(self):
        data = {
            'sniff_coin': 'invalid'  # Invalid data type
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A valid number is required.', response.data['sniff_coin'][0])
    
    