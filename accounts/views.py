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
        return Response({
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'level': user_profile.user_level,
            
        }, status=status.HTTP_200_OK)
    

class LeaderBoardView(APIView):
    def get(self, request, *args, **kwargs):
        wallet = Wallet.objects.all().order_by('-sniff_coin')[:100]
        serializer = WalletSerializer(wallet, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TelegramAuthAPIView(APIView):
    def parse_query_params(self, query_params):
        """Submethod to parse and decode query params."""
        parsed_data = {}
        for key, value in query_params.items():
            # Decode each key-value pair
            decoded_key = urllib.parse.unquote(key)
            decoded_value = urllib.parse.unquote(value)

            if decoded_key == "initData":
                # Parse the initData value and combine relevant data into a single dictionary
                init_data_dict = {}
                init_data_items = decoded_value.split('&')
                for item in init_data_items:
                    k, v = item.split('=', 1)
                    k = urllib.parse.unquote(k)
                    v = urllib.parse.unquote(v)

                    # If the key is 'user', we parse the JSON string and merge it into init_data_dict
                    if k == "user":
                        user_data = json.loads(v)
                        init_data_dict.update(user_data)
                    else:
                        init_data_dict[k] = v
                parsed_data.update(init_data_dict)
            else:
                parsed_data[decoded_key] = decoded_value

        return parsed_data
    

    # Danh sách các key được chấp nhận
    
    def get(self, request):
        # Parse and decode the query parameters using the submethod
        parsed_params = self.parse_query_params(request.GET)
        print("PARSED_PARAM>>>",parsed_params)
        # Initialize serializer with parsed parameters
        serializer = TelegramAuthSerializer(data=parsed_params)
        
        if serializer.is_valid():
            user, created = User.objects.get_or_create(
                username=serializer.validated_data['username'],
                defaults={
                    'first_name': serializer.validated_data['first_name'],
                    'last_name': serializer.validated_data['last_name'],
                }
            )
            refresh = RefreshToken.for_user(user)
            response_data = {
                'data': {
                    'token': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    },
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        "wallet": user.wallet.user_wallet_id  # Assuming user has a wallet field
                        # Thêm các trường khác nếu cần
                    }
                },
                'status': 200
            }
            return Response(response_data, status=status.HTTP_200_OK, content_type='application/json')
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
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
                "data": {
                    "token": {
                        "access": str(refresh.access_token),
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