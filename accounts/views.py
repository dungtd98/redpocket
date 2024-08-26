from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile
from wallet.models import Wallet
from wallet.serializers import WalletSerializer
from .serializers import *
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



from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.crypto import salted_hmac
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import SignInSerializer, CreateUserSerializer
from .ultis import generate_referral_code

class AuthService(APIView):
    def post(self, request, *args, **kwargs):
        sign_in_data = SignInSerializer(data=request.data)
        sign_in_data.is_valid(raise_exception=True)
        user = self.get_authenticated_user(sign_in_data.validated_data)
        if user:
            return self.handle_login(user)
        return Response({'detail': 'Authentication failed.'}, status=status.HTTP_400_BAD_REQUEST)

    def get_authenticated_user(self, sign_in_data):
        init_data = sign_in_data['initData']
        ref_code = sign_in_data['refCode']

        # Decode and parse the telegram init data
        user_telegram_info = self.get_telegram_init_data(init_data)
        id_telegram = user_telegram_info.get('id')
        
        # Check if the user already exists
        user = User.objects.filter(id_telegram=id_telegram).first()

        # If the user does not exist, create the user
        if not user:
            referral_code = self.generate_unique_referral_code()
            data_create = {
                'id_telegram': id_telegram,
                'username': user_telegram_info.get('username'),
                'first_name': user_telegram_info.get('first_name'),
                'last_name': user_telegram_info.get('last_name'),
                'referral_code': referral_code
            }
            user_serializer = CreateUserSerializer(data=data_create)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()

            if ref_code != 'none':
                referee = User.objects.filter(referral_code=ref_code).first()
                if referee:
                    # Assuming you have a Referral model/service to handle this
                    self.create_referral(referee.id, user.id)

        return user

    def generate_unique_referral_code(self):
        while True:
            code = generate_referral_code()
            if not User.objects.filter(referral_code=code).exists():
                return code

    def handle_login(self, user):
        access, refresh = self.generate_auth_tokens(user)

        return Response({
            'user': user,
            'token': {
                'access': access,
                'refresh': refresh
            }
        }, status=status.HTTP_200_OK)

    def generate_auth_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return str(access), str(refresh)

    def get_telegram_init_data(self, telegram_init_data):
        first_layer_init_data = dict(urllib.parse.parse_qsl(telegram_init_data))
        init_data = {k: json.loads(v) if self.is_json(v) else v for k, v in first_layer_init_data.items()}
        return init_data.get('user')

    def verify_telegram_init_data(self, telegram_init_data, bot_token=None):
        bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        encoded = urllib.parse.unquote(telegram_init_data)
        secret = salted_hmac('WebAppData', bot_token, algorithm='sha256')
        arr = encoded.split('&')
        hash_index = next(i for i, s in enumerate(arr) if s.startswith('hash='))
        hash_value = arr.pop(hash_index).split('=')[1]
        arr.sort()
        data_check_string = '\n'.join(arr)
        _hash = salted_hmac('sha256', secret, data_check_string).hexdigest()
        return _hash == hash_value

    def is_json(self, myjson):
        try:
            json.loads(myjson)
        except ValueError:
            return False
        return True


def index(request):
    return render(request, 'index.html')