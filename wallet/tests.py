from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from django.urls import reverse
from .models import Wallet, UserStake, GiveawayPouch
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
import json
from .views import CreateGiveawayPouchView
from .models import GiveawayPouch
from rest_framework import status

# v=spf1 include:_spf.google.com include:amazonses.com ~all
User = get_user_model()
class CreateGiveawayPouchViewTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.view = CreateGiveawayPouchView.as_view()
        self.url = '/create-giveaway-pouch/'

    @patch('wallet.views.check_can_share_pouch', return_value=True)
    @patch('wallet.views.GiveawayPouchSerializer.is_valid', return_value=True)
    @patch('wallet.views.GiveawayPouchSerializer.save')
    @patch('wallet.views.GiveawayPouchSerializer.data', new_callable=dict)
    @patch('wallet.views.add_tokens_to_user.apply_async')
    def test_create_giveaway_pouch_success(self, mock_apply_async, mock_data, mock_save, mock_is_valid, mock_check_can_share_pouch):
        mock_data.update({
            'id': 1,
            'user': self.user.id,
            'amount': 100,
            'created_at': '2023-01-01T00:00:00Z',
            'updated_at': '2023-01-01T00:00:00Z'
        })
        request = self.factory.post(self.url, {'amount': 100})
        request.user = self.user

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['data']['amount'], 100)

    @patch('wallet.views.check_can_share_pouch', return_value=False)
    def test_create_giveaway_pouch_daily_limit_reached(self, mock_check_can_share_pouch):
        request = self.factory.post(self.url, {'amount': 100})
        request.user = self.user

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'You have reached the daily limit of opening pouch.')

    @patch('wallet.views.check_can_share_pouch', return_value=True)
    @patch('wallet.views.GiveawayPouchSerializer.is_valid', return_value=False)
    @patch('wallet.views.GiveawayPouchSerializer.errors', new_callable=dict)
    @patch('wallet.views.add_tokens_to_user.apply_async')
    def test_create_giveaway_pouch_invalid_data(self, mock_apply_async, mock_errors, mock_is_valid, mock_check_can_share_pouch):
        mock_errors.update({'amount': ['This field is required.']})
        request = self.factory.post(self.url, {})
        request.user = self.user

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['amount'], ['This field is required.'])


class CreateStakeViewTests(APITestCase):
    """
    Test case for the CreateStakeView.
    Methods:
    - setUp: Set up the test case by creating a test user, wallet, and setting up the client.
    - test_create_stake_success: Test the successful creation of a stake.
    - test_create_stake_failure: Test the failure of creating a stake due to missing duration field.
    """
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Check if the wallet already exists for the user
        self.wallet, created = Wallet.objects.get_or_create(user=self.user, defaults={'sniff_coin': 1000})
        
        self.client.force_authenticate(user=self.user)
        self.url = reverse('create-stake')  # Adjust the URL name as needed

    def test_create_stake_success(self):
        data = {
            "amount": 100,
            "duration": 7
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['data']['amount_staked'], 100)
        self.assertEqual(response.data['data']['user_id'], self.user.id)

    def test_create_stake_failure(self):
        data = {
            "amount": 100
            # Missing 'duration' field
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('duration', response.data)


class GetActiveStakeViewTests(APITestCase):
    """
    Test case for the GetActiveStakeView.
    Methods:
    - setUp: Set up the necessary objects and configurations before each test.
    - test_get_active_stake: Test the retrieval of active stake.
    - test_get_active_stake_no_active_stake: Test the retrieval of active stake when there is no active stake.
    - test_get_active_stake_earnings: Test the retrieval of active stake earnings.
    """
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Check if the wallet already exists for the user
        self.wallet, created = Wallet.objects.get_or_create(user=self.user, defaults={'sniff_coin': 10})
        
        self.stake = UserStake.objects.create(
            user=self.user,
            amount=100,
            status='active',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=30)
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('get-active-stake')  # Adjust the URL name as per your routing

    def test_get_active_stake(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['data']['id'], self.stake.id)
        self.assertEqual(response.data['data']['amount'], self.stake.amount)

    def test_get_active_stake_no_active_stake(self):
        self.stake.status = 'inactive'
        self.stake.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data'], None)

    def test_get_active_stake_earnings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['earnings'], self.wallet.sniff_coin * 10)


class ClaimPouchTokenViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.pouch = GiveawayPouch.objects.create(user=self.user, amount=100, expired_date=timezone.now() + timezone.timedelta(hours=1))
        self.url = reverse('claim-pouch-token')

    @patch('wallet.views.check_can_open_pouch')
    def test_reached_daily_limit(self, mock_check_can_open_pouch):
        mock_check_can_open_pouch.return_value = False
        response = self.client.post(self.url, {'idCoinPouch': self.pouch.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "You have reached the daily limit of opening pouch.")

    @patch('wallet.views.check_can_open_pouch')
    def test_pouch_expired(self, mock_check_can_open_pouch):
        mock_check_can_open_pouch.return_value = True
        self.pouch.expired_date = timezone.now() - timezone.timedelta(hours=1)
        self.pouch.save()
        response = self.client.post(self.url, {'idCoinPouch': self.pouch.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "This pouch has expired.")

    @patch('wallet.views.check_can_open_pouch')
    @patch('wallet.views.get_from_redis')
    @patch('wallet.views.save_to_redis')
    @patch('wallet.views.get_random_value_from_array')
    def test_successful_claim(self, mock_get_random_value_from_array, mock_save_to_redis, mock_get_from_redis, mock_check_can_open_pouch):
        mock_check_can_open_pouch.return_value = True
        mock_get_from_redis.return_value = json.dumps({"values_array": [10, 20, 30]})
        mock_get_random_value_from_array.return_value = (10, [20, 30])
        response = self.client.post(self.url, {'idCoinPouch': self.pouch.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['coin_value'], 10)