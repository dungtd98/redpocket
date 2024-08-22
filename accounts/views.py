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
from .models import User  # Giả sử bạn đã có model User

def telegram_login_callback(request):
    bot_token = '5899297704:AAHDQkjvDcUlSSHzmhLwRQk5-KQ17VstR58'
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    hash_check = request.GET.get('hash')
    payload = request.GET.get('payload')
    
    # Decode payload
    payload_data = json.loads(base64.b64decode(payload))

    # Verify hash
    data_check = hmac.new(secret_key, msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()
    
    if data_check != hash_check:
        return JsonResponse({'error': 'Invalid hash.'}, status=400)
    
    # Extract user information
    user_info = payload_data['user']
    user_id = user_info['id']
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')
    username = user_info.get('username', '')

    # Create or get user
    user, created = User.objects.get_or_create(
        telegram_id=user_id,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'username': username
        }
    )

    # Generate JWT token
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    
    return JsonResponse({'token': token})
    

from django.shortcuts import redirect

def redirect_to_telegram_oauth(request):
    bot_id = '5899297704'
    scope = 'identity'
    public_key = 'YOUR_PUBLIC_KEY'
    nonce = 'RANDOM_NONCE'

    oauth_url = f"https://oauth.telegram.org/auth?bot_id={bot_id}&scope={scope}&public_key={public_key}&nonce={nonce}"
    return redirect(oauth_url)

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return JsonResponse({'message': 'This is a protected view only for authenticated users.'})
import jwt

class TelegramAuthView(APIView):

    def get(self, request, *args, **kwargs):
        bot_token = '5899297704:AAHDQkjvDcUlSSHzmhLwRQk5-KQ17VstR58'
        secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
        print(request.query_params)
        hash = request.query_params.get('hash')
        payload = json.loads(base64.b64decode(request.GET.get('payload')).decode('utf-8'))

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
    
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')