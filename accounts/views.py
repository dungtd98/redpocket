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
class TelegramLoginAPIView(APIView):
    def post(self, request):
        data = request.data
        TELEGRAM_BOT_TOKEN = '5899297704:AAEaS1T9NJ64Q0nQ-uEf3-XEmvJeTLAtgeg'
        secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()

        auth_date = data.get('auth_date')
        hash_telegram = data.get('hash')

        check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])

        hash_check = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

        if hash_check != hash_telegram:
            return Response({'detail': 'Invalid data received from Telegram.'}, status=status.HTTP_400_BAD_REQUEST)

        if time.time() - int(auth_date) > 86400:
            return Response({'detail': 'Authentication data is too old.'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = data.get('user')['id']
        first_name = data.get('user')['first_name']
        last_name = data.get('user')['last_name']
        username = data.get('user')['username']

        user, created = User.objects.get_or_create(username=username, defaults={
            'first_name': first_name,
            'last_name': last_name,
            'password': User.objects.make_random_password()
        })

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')