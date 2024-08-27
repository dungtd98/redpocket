
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GiveawayPouchSerializer, UserStakeSerializer, TaskSerializer
from .models import GiveawayPouch, Wallet, UserStake, Task, UserLevel
from .ultis import *
import json
from django.utils import timezone
from .tasks import add_tokens_to_user
from datetime import timedelta


class CreateGiveawayPouchView(APIView):
    def post(self, request, format=None):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = GiveawayPouchSerializer(data=data)
        can_share_pouch = can_open_pouch(request.user)
        if not can_share_pouch:
            return Response({"message": "You have reached the daily limit of opening pouch."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            pouch_sniff_coin = serializer.validated_data.get("amount")
            
            pouch_coin_array = json.dumps({"values_array": divide_into_percentage_array(pouch_sniff_coin)})
            serializer.save()
            redis_key_name = f"giveaway_pouch_{serializer.data.get('id')}"
            redis_value = json.dumps({
                "values_array": pouch_coin_array,
                "init_value": int(pouch_sniff_coin)
            })
            save_to_redis(redis_key_name, redis_value, 1800)
            add_tokens_to_user.apply_async(args=[request.user.id, serializer.data.get('id')], countdown=1800)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClaimPouchTokenView(APIView):
    def get(self, request, *args, **kwargs):
        """
        This API for open pouch and get random sniff coin
        """
        can_open_pouch = can_open_pouch(request.user)
        if not can_open_pouch:
            return Response({"message": "You have reached the daily limit of opening pouch."}, status=status.HTTP_400_BAD_REQUEST)
        pouch_id = request.query_params.get('pouch_id')
        pouch = GiveawayPouch.objects.get(id=pouch_id)
        pouch_expired_date = pouch.expired_date
        if pouch_expired_date < timezone.now():
            return Response({"message": "This pouch has expired."}, status=status.HTTP_400_BAD_REQUEST)
        pouch_coin_value = json.loads(get_from_redis(f"giveaway_pouch_{pouch_id}"))
        pouch_coin_array = pouch_coin_value.get("values_array")
        coin_value, pouch_coin_array = get_random_value_from_array(pouch_coin_array)
        pouch_coin_value["values_array"] = pouch_coin_array
        save_to_redis(f"giveaway_pouch_{pouch_id}", pouch_coin_value, 86400)
        save_to_redis(f"claim_pouch_{pouch_id}_{request.user.id}", coin_value, 86400)
        return Response(pouch_coin_array, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        This API handle claim sniff coin from pouch
        """
        pouch_id = request.data.get('pouch_id')
        claimed_coin = get_from_redis(f"claim_pouch_{pouch_id}_{request.user.id}")
        if claimed_coin is None:
            return Response({"message": "You have either not claimed any coin from this pouch or the pouch has expired."}, status=status.HTTP_400_BAD_REQUEST)
        wallet = Wallet.objects.get(user=request.user)
        wallet.sniff_coin += claimed_coin
        wallet.save()
        return Response({"message": f"You have successfully claimed {claimed_coin} sniff coin from the pouch."}, status=status.HTTP_200_OK)


class GetPouchListInfoView(APIView):
    def get(self, request, *args, **kwargs):
        sent_pouches = GiveawayPouch.objects.filter(user=request.user)
        unopened_pouches = get_values_with_key_pattern(f"claim_pouch_*_{request.user.id}")

        response_data = []
        for pouch in sent_pouches:
            redis_data = get_from_redis(f"giveaway_pouch_{pouch.id}")
            if redis_data:
                values_array = json.loads(redis_data).get("values_array", [])
            else:
                values_array = []

            pouch_data = {
                "id": pouch.id,
                "amount": pouch.amount,
                "amount_claim": 0,
                "owner_id": pouch.user.id,
                "status": "OPEN" if pouch.expired_date > timezone.now() else "CLAIM",
                "time_end": pouch.expired_date.isoformat(),
                "opened": len(values_array)
            }
            response_data.append(pouch_data)

        for unopened_pouch in unopened_pouches:
            pouch_data = {
                "id": unopened_pouch['id'],
                "amount": unopened_pouch['amount'],
                "amount_claim": unopened_pouch['amount_claim'],
                "owner_id": unopened_pouch['owner_id'],
                "status": unopened_pouch['status'],
            }
            response_data.append(pouch_data)

        return Response(response_data, status=status.HTTP_200_OK)
    

class CreateStakeView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = UserStakeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetActiveStakeView(APIView):
    def get(self, request, *args, **kwargs):
        active_stakes = UserStake.objects.filter(end_datetime__gt=timezone.now())
        return Response(UserStakeSerializer(active_stakes, many=True).data, status=status.HTTP_200_OK)

class GetActiveTaskView(APIView):
    def get(self, request, *args, **kwargs):
        active_tasks = Task.objects.filter(task_expired__gt=timezone.now())
        return Response(TaskSerializer(active_tasks, many=True).data, status=status.HTTP_200_OK)

class ClaimNewUserAPIView(APIView):
    def post(self, request, *args, **kwargs):
        wallet = Wallet.objects.get(user=request.user)
        wallet.sniff_point += 100
        wallet.save()
        user_level = UserLevel.objects.get(user=request.user)
        request.user.claim_expire = timezone.now() + timedelta(minutes=30)
        request.user.save()
        user_data = {
            "id": request.user.id,
            "created_at": request.user.date_joined.isoformat(),
            "updated_at": request.user.last_login.isoformat() if request.user.last_login else None,
            "id_telegram": request.user.telegram_id,
            "username": request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "balance_sniff_point": wallet.sniff_point,
            "balance_sniff_point_ath": wallet.sniff_point,  
            "balance_sniff_coin": str(wallet.sniff_coin),
            "balance_scratch_card": 0,  
            "balance_usdt": "0.00",  
            "trigger_up_level": False,  
            "referral_code": request.user.referral_code,
            "refresh_token": "ABCD",  
            "wallet": None,  
            "network": None,  
            "age_wallet": None,  
            "age_telegram": None,  
            "level_id_old": 0,  
            "level_id": 0,  
            "claim_expire": request.user.claim_expire.isoformat() if request.user.claim_expire else None,
            "level": {
                "id": user_level.id,
                "created_at": user_level.created_at.isoformat(),
                "updated_at": user_level.updated_at.isoformat(),
                "level_number": user_level.level_number,
                "level_name": user_level.level_name,
                "require_balance": user_level.require_balance,
                "cost_level_up": user_level.cost_level_up,
                "boost": user_level.boost,
                "send_envelope": user_level.send_envelope
            },
            "histories_open_coin_pouchs": [],  
            "histories_send_coin_pouchs": [],  
            "createdCountPouchToday": 0,  
            "openedCountPouchToday": 0,  
            "createdCountPouch": 0,  
            "trigger_up_level_data": None,  
            "limitAmountCoinPouchToday": 100000,  
            "totalAmountPouchToday": 0  
        }

        response = {
            "status": "SUCCESS",
            "statusCode": 200,
            "data": {
                "user": user_data
            },
            "message": "CLAIM_NEW_USER_SUCCESSFULLY"
        }

        return Response(response, status=status.HTTP_200_OK)