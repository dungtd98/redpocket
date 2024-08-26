from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile
from wallet.models import Wallet
from wallet.serializers import WalletSerializer
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
    

import hashlib
import hmac
import json
import base64
from django.http import JsonResponse
from django.conf import settings
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
import jwt
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import urllib.parse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return JsonResponse({'message': 'This is a protected view only for authenticated users.'})

import time
class TelegramAuthViewV1(APIView):

    def get(self, request, *args, **kwargs):
        bot_token = '5899297704:AAHDQkjvDcUlSSHzmhLwRQk5-KQ17VstR58'
        secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
        print(request.query_params)
        hash = request.query_params.get('hash')
        payload = json.loads(base64.b64decode(request.GET.get('payload',"")).decode('utf-8'))
        
        check_hash = hmac.new(secret_key, json.dumps(payload, separators=(',', ':')).encode('utf-8'), hashlib.sha256).hexdigest()

        if hash != check_hash:
            return Response({'error': 'Invalid hash'}, status=status.HTTP_400_BAD_REQUEST)

        user_data = payload['user']
        user, created = User.objects.get_or_create(
            telegram_id=user_data['id'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data.get('last_name', ''),
                'username': user_data.get('username', ''),
            }
        )

        # Tạo JWT
        jwt_payload = {
            'user_id': user.id,
            'username': user.username,
        }
        token = jwt.encode(jwt_payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({'token': token}, status=status.HTTP_200_OK)
    
class TelegramAuthViewV2(APIView):
    def post(self, request):
        init_data = request.data.get('initData')

        if not init_data:
            return Response({'error': 'initData is required'}, status=400)

        # Decode the URL-encoded initData
        decoded_data = urllib.parse.unquote(init_data)

        # Parse the decoded data into a dictionary
        parsed_data = urllib.parse.parse_qs(decoded_data)

        # Extract hash and auth_date from the parsed data
        telegram_hash = parsed_data.get('hash', [None])[0]
        auth_date = parsed_data.get('auth_date', [None])[0]
        print(telegram_hash)
        # Step 1: Verify request time
        if time.time() - int(auth_date) > 86400:  # 24 hours
            return Response({'error': 'Authentication expired'}, status=status.HTTP_403_FORBIDDEN)

        # Step 2: Generate data_check_string
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(parsed_data.items()) if k != 'hash'])
        
        # Step 3: Calculate the secret key using your bot token
        TELEGRAM_BOT_TOKEN = "5882917777:AAEaS1T9NJ64Q0nQ-uEf3-XEmvJeTLAtgeg"
        secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode('utf-8')).digest()
        
        # Step 4: Calculate the hash
        calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # Step 5: Compare calculated hash with the provided hash
        if calculated_hash != telegram_hash:
            return Response({'error': 'Invalid hash'}, status=status.HTTP_403_FORBIDDEN)
        
        # Step 6: Get or create the user
        telegram_id = parsed_data.get('id')[0]
        first_name = parsed_data.get('first_name')[0]
        last_name = parsed_data.get('last_name', '')[0]
        username = parsed_data.get('username', '')[0]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'first_name': first_name, 'last_name': last_name, 'email': '', 'password': ''}
        )

        # Step 7: Generate JWT token using SimpleJWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
        }, status=status.HTTP_200_OK, content_type='application/json')
    
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')