from .models import User
from .serializers import UpdateUserDtoSerializer, CreateUserDtoSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import random
import string

def generate_referral_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_telegram_age(telegram_id):
    # Implement logic to calculate Telegram age
    pass

def get_wallet_age(wallet, network):
    # Implement logic to calculate Wallet age
    pass
class AuthService:
    def __init__(self):
        self.user_service = UserService()  # Implement the user service

    def generate_auth_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return {
            'access': str(access),
            'refresh': str(refresh),
        }

    def handle_login(self, user, wallet=None):
        tokens = self.generate_auth_tokens(user)
        data_update = {}

        if wallet and not user.wallet:
            age_wallet = get_wallet_age(wallet, 'TON')
            age_telegram = get_telegram_age(user.id_telegram)
            data_update.update({
                'wallet': wallet,
                'age_wallet': age_wallet,
                'age_telegram': age_telegram,
                'balance_sniff_point': 100,
                'balance_sniff_coin': age_wallet + age_telegram * 365,
            })

        if data_update:
            serializer = UpdateUserDtoSerializer(user, data=data_update, partial=True)
            if serializer.is_valid():
                serializer.save()

        user = self.user_service.get_user_info(user.id)
        return {'user': user, 'token': tokens}

    def get_authenticated_user(self, sign_in_dto):
        initData = sign_in_dto.get('initData')
        refCode = sign_in_dto.get('refCode', 'none')
        user_telegram_info = self.get_telegram_init_data(initData)
        user = self.user_service.get_user_by_telegram_id(user_telegram_info['id'])

        if not user:
            referral_code = generate_referral_code()
            while self.user_service.is_referral_code_exists(referral_code):
                referral_code = generate_referral_code()

            create_user_data = {
                'id_telegram': user_telegram_info['id'],
                'username': user_telegram_info['username'],
                'first_name': user_telegram_info['first_name'],
                'last_name': user_telegram_info.get('last_name', ''),
                'referral_code': referral_code
            }
            serializer = CreateUserDtoSerializer(data=create_user_data)
            if serializer.is_valid():
                user = serializer.save()

            if refCode != 'none':
                referee = self.user_service.get_user_by_referral_code(refCode)
                if referee:
                    self.referral_service.create_referral(referee.id, user.id)

        return user

    def get_telegram_init_data(self, telegram_init_data):
        # Parsing logic as per your requirement
        return parsed_data
