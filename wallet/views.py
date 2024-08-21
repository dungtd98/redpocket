
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GiveawayPouchSerializer
from .models import GiveawayPouch, Wallet
from .ultis import *
import json
from django.utils import timezone



class CreateGiveawayPouchView(APIView):
    def post(self, request, format=None):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = GiveawayPouchSerializer(data=data)
        if serializer.is_valid():
            pouch_sniff_coin = serializer.validated_data.get("sniff_coin")
            
            pouch_coin_array = json.dumps({"values_array": divide_into_percentage_array(pouch_sniff_coin)})
            serializer.save()
            print(serializer.validated_data)
            redis_key_name = f"giveaway_pouch_{serializer.data.get('id')}"
            save_to_redis(redis_key_name, pouch_coin_array, 1800)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClaimPouchTokenView(APIView):
    def get(self, request, *args, **kwargs):
        """
        This API for open pouch and get random sniff coin
        """
        pouch_id = request.query_params.get('pouch_id')
        pouch = GiveawayPouch.objects.get(id=pouch_id)
        pouch_expired_date = pouch.expired_date
        if pouch_expired_date < timezone.now():
            return Response({"message": "This pouch has expired."}, status=status.HTTP_400_BAD_REQUEST)
        pouch_coin_array = get_from_redis(f"giveaway_pouch_{pouch_id}")
        coin_value, pouch_coin_array = get_random_value_from_array(pouch_coin_array)
        save_to_redis(f"giveaway_pouch_{pouch_id}", pouch_coin_array, 1800)
        save_to_redis(f"claim_pouch_{pouch_id}_{request.user.id}", coin_value, 86400)
        return Response(pouch_coin_array, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        pouch_id = request.data.get('pouch_id')
        claimed_coin = get_from_redis(f"claim_pouch_{pouch_id}_{request.user.id}")
        if claimed_coin is None:
            return Response({"message": "You have either not claimed any coin from this pouch or the pouch has expired."}, status=status.HTTP_400_BAD_REQUEST)
        wallet = Wallet.objects.get(user=request.user)
        wallet.sniff_coin += claimed_coin
        wallet.save()
        return Response({"message": f"You have successfully claimed {claimed_coin} sniff coin from the pouch."}, status=status.HTTP_200_OK)

