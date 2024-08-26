from .models import UserProfile
from rest_framework import serializers

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

# serializers.py

from rest_framework import serializers
import hashlib
import hmac
import time

class TelegramAuthSerializer(serializers.Serializer):
    id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    auth_date = serializers.CharField()
    hash = serializers.CharField()

    def validate(self, data):
        secret_key = '5882917777:AAEaS1T9NJ64Q0nQ-uEf3-XEmvJeTLAtgeg'  # Thay bằng token của bot của bạn

        # Chuẩn bị chuỗi dữ liệu để xác minh
        check_string_fitered_data = self.filter_check_string(data)
        check_string = '\n'.join(
            [f'{k}={v}' for k, v in sorted(check_string_fitered_data.items()) if k != 'hash']
        )
        print("Cheeck string",check_string)
        # Tạo hash để so sánh
        secret_key_bytes = hashlib.sha256(secret_key.encode()).digest()
        calculated_hash = hmac.new(secret_key_bytes, check_string.encode(), hashlib.sha256).hexdigest()
        print("calculated_hash",calculated_hash)
        if calculated_hash != data['hash']:
            raise serializers.ValidationError("Invalid hash. Authentication failed.")

        # Kiểm tra thời gian xác thực (auth_date)
        if time.time() - int(data['auth_date']) > 86400:  # 86400 giây = 24 giờ
            raise serializers.ValidationError("Auth date is too old.")

        return data

    def filter_check_string(self, data):
        """Filter the dictionary to only keep allowed keys."""
        allowed_keys = {'id', 'first_name', 'last_name', 'username', 'auth_date', 'hash'}
        return {key: value for key, value in data.items() if key in allowed_keys}