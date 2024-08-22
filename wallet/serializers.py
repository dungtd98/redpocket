import decimal
from .models import Wallet, GiveawayPouch, UserStake, Task
from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()

class WalletSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    class Meta:
        model = Wallet
        fields = '__all__'

class GiveawayPouchSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiveawayPouch
        fields = '__all__'

    def validate_sniff_coin(self, value):
        # Get the current user from the context
        print(value, self.initial_data)
        
        user = self.initial_data.get('user')
        wallet = Wallet.objects.get(user=user)
        max_sniff_coin = wallet.sniff_coin * decimal.Decimal('0.2')
        if value > max_sniff_coin:
            raise serializers.ValidationError(f"You can only allocate up to 20% ({max_sniff_coin}) of your wallet's sniff coin.")
        
        return value

class UserStakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStake
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'