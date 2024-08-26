from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile
from wallet.models import Wallet
from wallet.serializers import WalletSerializer
from .serializers import TelegramAuthSerializer
import urllib.parse
import json

User = get_user_model()


class GetUserProfileView(APIView):
    def get(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        wallet = Wallet.objects.get(user=request.user)

        response_data = {
            "status": "SUCCESS",
            "statusCode": 200,
            "data": {
                "id": request.user.id,
                "created_at": request.user.date_joined.isoformat(),
                "updated_at": request.user.last_login.isoformat() if request.user.last_login else None,
                "id_telegram": request.user.telegram_id,
                "username": request.user.username,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "balance_sniff_point": wallet.sniff_point,
                "balance_sniff_point_ath": 0,  # Example static value
                "balance_sniff_coin": wallet.sniff_coin,
                "balance_scratch_card": 0,  # Example static value
                "balance_usdt": "0.00",  # Example static value
                "trigger_up_level": False,  # Example static value
                "referral_code": request.user.referral_code,
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NCwiaWRfdGVsZWdyYW0iOjU5NjQxODQzMDksImlhdCI6MTcyNDY1ODU5OCwiZXhwIjoxNzI5ODQyNTk4fQ.feCY37ptXTbe5WKp9R2oRGawmrPGuCiC8bOIHAxxrRA",  # Example static value
                "wallet": None,  # Example static value
                "network": None,  # Example static value
                "age_wallet": None,  # Example static value
                "age_telegram": None,  # Example static value
                "level_id_old": 0,  # Example static value
                "level_id": 0,  # Example static value
                "claim_expire": None,  # Example static value
                "level": {
                    "id": 1,  # Example static value
                    "created_at": "2024-08-26T07:09:24.978Z",  # Example static value
                    "updated_at": "2024-08-26T07:09:24.978Z",  # Example static value
                    "level_number": 0,  # Example static value
                    "level_name": "Level 0",  # Example static value
                    "require_balance": 0,  # Example static value
                    "cost_level_up": 0,  # Example static value
                    "boost": 5,  # Example static value
                    "send_envelope": 1  # Example static value
                },
                "histories_open_coin_pouchs": [],  # Example static value
                "histories_send_coin_pouchs": [],  # Example static value
                "createdCountPouchToday": 0,  # Example static value
                "openedCountPouchToday": 0,  # Example static value
                "createdCountPouch": 0,  # Example static value
                "trigger_up_level_data": None,  # Example static value
                "limitAmountCoinPouchToday": 100000,  # Example static value
                "totalAmountPouchToday": 0  # Example static value
            },
            "message": "GET_INFOR_USER_SUCCESSFULLY"
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

class LeaderBoardView(APIView):
    def get(self, request, *args, **kwargs):
        wallet = Wallet.objects.all().order_by('-sniff_coin')[:100]
        serializer = WalletSerializer(wallet, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

import hashlib
import hmac
import time
TELEGRAM_BOT_TOKEN = "5882917777:AAEaS1T9NJ64Q0nQ-uEf3-XEmvJeTLAtgeg"

class TelegramLoginAPIView(APIView):
    def post(self, request):
        init_data = request.data.get("initData")
        ref_code = request.data.get("refCode", "none")

        # Verify the authenticity of the Telegram initialization data
        if not self.verify_telegram_init_data(init_data, TELEGRAM_BOT_TOKEN):
            return Response({"detail": "Invalid Telegram signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Extract parameters from init_data
        params = dict(item.split('=') for item in urllib.parse.unquote(init_data).split('&'))
        user_data = json.loads(params['user'])

        # Here you would typically create or get the user based on Telegram user data
        user = self.get_or_create_user(params['user'])

        # Create a JWT token for the user
        refresh = RefreshToken.for_user(user)
        response_data = {
            "status": 200,
            "data": {
                "token": {
                    "access_token": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "email": user.email,
                    "telegram_id":user_data['id']
                }
            }
            
        }
        return Response(response_data, status=status.HTTP_200_OK, content_type='application/json')

    def verify_telegram_init_data(self, telegram_init_data: str, bot_token: str) -> bool:
        # Decode the URL-encoded string
        encoded = urllib.parse.unquote(telegram_init_data)

        # Create the secret HMAC using the bot token and 'WebAppData'
        secret = hmac.new(b'WebAppData', bot_token.encode('utf-8'), hashlib.sha256)

        # Split the encoded data into an array of key-value pairs
        arr = encoded.split('&')

        # Find the index of the 'hash' parameter
        hash_index = next(i for i, s in enumerate(arr) if s.startswith('hash='))
        
        # Extract the hash value and remove it from the array
        hash_value = arr.pop(hash_index).split('=')[1]

        # Sort the remaining key-value pairs
        arr.sort()

        # Create the data check string
        data_check_string = '\n'.join(arr)

        # Calculate the HMAC for the data check string
        calculated_hash = hmac.new(secret.digest(), data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

        # Compare the calculated hash with the provided hash
        return calculated_hash == hash_value

    def get_or_create_user(self, user_data):
        user_info = json.loads(user_data)
        # Here you would typically fetch the user from the database or create a new one
        # This is a simplified example, adjust according to your user model
        user, created = User.objects.get_or_create(
            # telegram_id=user_info['id'],
            defaults={
                'first_name': user_info['first_name'],
                'last_name': user_info.get('last_name', ''),
                'username': user_info.get('username', ''),
            }
        )
        return user
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')