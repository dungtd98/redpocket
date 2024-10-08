from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from wallet.models import Wallet
from wallet.serializers import WalletSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import urllib.parse
import json
from .ultis import count_open_pouch, count_share_pouch
import hashlib
import hmac


User = get_user_model()


class GetUserProfileView(APIView):
    @swagger_auto_schema(
        operation_description="Get user profile",
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type="object",
                    properties={
                        "status": openapi.Schema(type="string"),
                        "statusCode": openapi.Schema(type="integer"),
                        "data": openapi.Schema(
                            type="object",
                            properties={
                                "id": openapi.Schema(type="integer"),
                                "created_at": openapi.Schema(type="string"),
                                "updated_at": openapi.Schema(type="string", nullable=True),
                                "id_telegram": openapi.Schema(type="integer"),
                                "username": openapi.Schema(type="string"),
                                "first_name": openapi.Schema(type="string"),
                                "last_name": openapi.Schema(type="string"),
                                "balance_sniff_point": openapi.Schema(type="integer"),
                                "balance_sniff_point_ath": openapi.Schema(type="integer"),
                                "balance_sniff_coin": openapi.Schema(type="integer"),
                                "balance_scratch_card": openapi.Schema(type="integer"),
                                "balance_usdt": openapi.Schema(type="string"),
                                "trigger_up_level": openapi.Schema(type="boolean"),
                                "referral_code": openapi.Schema(type="string"),
                                "wallet": openapi.Schema(type="object", nullable=True),
                                "network": openapi.Schema(type="object", nullable=True),
                                "age_wallet": openapi.Schema(type="object", nullable=True),
                                "age_telegram": openapi.Schema(type="object", nullable=True),
                                "level_id_old": openapi.Schema(type="integer"),
                                "level_id": openapi.Schema(type="integer"),
                                "claim_expire": openapi.Schema(type="string", nullable=True),
                                "level": openapi.Schema(
                                    type="object",
                                    properties={
                                        "id": openapi.Schema(type="integer"),
                                        "created_at": openapi.Schema(type="string"),
                                        "updated_at": openapi.Schema(type="string"),
                                        "level_number": openapi.Schema(type="integer"),
                                        "level_name": openapi.Schema(type="string"),
                                        "require_balance": openapi.Schema(type="integer"),
                                        "cost_level_up": openapi.Schema(type="integer"),
                                        "boost": openapi.Schema(type="integer"),
                                        "send_envelope": openapi.Schema(type="integer"),
                                    },
                                ),
                                "histories_open_coin_pouchs": openapi.Schema(type="array", items=openapi.Items(type=openapi.TYPE_STRING)),
                                "histories_send_coin_pouchs": openapi.Schema(type="array", items=openapi.Items(type=openapi.TYPE_STRING)),
                                "createdCountPouchToday": openapi.Schema(type="integer"),
                                "openedCountPouchToday": openapi.Schema(type="integer"),
                                "createdCountPouch": openapi.Schema(type="integer"),
                                "trigger_up_level_data": openapi.Schema(type="object", nullable=True),
                                "limitAmountCoinPouchToday": openapi.Schema(type="integer"),
                                "totalAmountPouchToday": openapi.Schema(type="integer"),
                            },
                        ),
                        "message": openapi.Schema(type="string"),
                    },
                ),
            ),
        },
    )

    def get(self, request):
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
                "balance_sniff_point_ath": 0, 
                "balance_sniff_coin": wallet.sniff_coin,
                "balance_scratch_card": 0, 
                "balance_usdt": "0.00", 
                "trigger_up_level": False, 
                "referral_code": request.user.referral_code,
                "wallet": None, 
                "network": None, 
                "age_wallet": None, 
                "age_telegram": None, 
                "level_id_old": 0, 
                "level_id": 0, 
                "claim_expire": request.user.claim_expire.isoformat() if request.user.claim_expire else None, 
                "level": {
                    "id": 1, 
                    "created_at": "2024-08-26T07:09:24.978Z", 
                    "updated_at": "2024-08-26T07:09:24.978Z", 
                    "level_number": 0, 
                    "level_name": "Level 0", 
                    "require_balance": 0, 
                    "cost_level_up": 0, 
                    "boost": 5, 
                    "send_envelope": 1 
                },
                "histories_open_coin_pouchs": [], 
                "histories_send_coin_pouchs": [], 
                "createdCountPouchToday": count_share_pouch(request.user), 
                "openedCountPouchToday": count_open_pouch(request.user), 
                "createdCountPouch": request.user.daily_limit_share_pouch, 
                "trigger_up_level_data": None, 
                "limitAmountCoinPouchToday": 100000, 
                "totalAmountPouchToday": 0 
            },
            "message": "GET_INFOR_USER_SUCCESSFULLY"
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

class LeaderBoardView(APIView):
    def get(self, request, *args, **kwargs):
        wallet = Wallet.objects.all().order_by('-sniff_coin')[:100]
        serializer = WalletSerializer(wallet, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        user = self.get_or_create_user(params['user'])
        if ref_code != "none":
            user.invited_refcode = ref_code
            user.save()
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
                    "telegram_id":user_data['id']
                }
            }
            
        }
        return Response(response_data, status=status.HTTP_200_OK, content_type='application/json')

    def verify_telegram_init_data(self, telegram_init_data: str, bot_token: str) -> bool:
        encoded = urllib.parse.unquote(telegram_init_data)
        secret = hmac.new(b'WebAppData', bot_token.encode('utf-8'), hashlib.sha256)
        arr = encoded.split('&')
        hash_index = next(i for i, s in enumerate(arr) if s.startswith('hash='))
        hash_value = arr.pop(hash_index).split('=')[1]
        arr.sort()
        data_check_string = '\n'.join(arr)
        calculated_hash = hmac.new(secret.digest(), data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return calculated_hash == hash_value

    def get_or_create_user(self, user_data):
        user_info = json.loads(user_data)
        user, created = User.objects.get_or_create(
            telegram_id=user_info['id'],
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