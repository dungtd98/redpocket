from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile
from wallet.models import Wallet
from wallet.serializers import WalletSerializer
User = get_user_model()

class TelegramAuthView(APIView):
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # Create or update the user based on Telegram data
        user, created = User.objects.get_or_create(username=telegram_id, defaults={
            'first_name': first_name,
            'last_name': last_name
        })

        # If the user was created, you might set more fields like setting a random password
        if created:
            user.set_unusable_password()
            user.save()

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(user)
        
        # Return the token to the user
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


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
    