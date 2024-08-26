
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GiveawayPouchSerializer, UserStakeSerializer, TaskSerializer
from .models import GiveawayPouch, Wallet, UserStake, Task
from .ultis import *
import json
from django.utils import timezone
from .tasks import add_tokens_to_user

class CreateGiveawayPouchView(APIView):
    def post(self, request, format=None):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = GiveawayPouchSerializer(data=data)
        can_share_pouch = can_open_pouch(request.user)
        if not can_share_pouch:
            return Response({"message": "You have reached the daily limit of opening pouch."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            pouch_sniff_coin = serializer.validated_data.get("sniff_coin")
            
            pouch_coin_array = json.dumps({"values_array": divide_into_percentage_array(pouch_sniff_coin)})
            serializer.save()
            redis_key_name = f"giveaway_pouch_{serializer.data.get('id')}"
            redis_value = json.dumps({
                "values_array": pouch_coin_array,
                "init_value": pouch_sniff_coin
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
            pouch_data = {
                "id": pouch.id,
                "amount": pouch.sniff_coin,
                "amount_claim": sum(json.loads(get_from_redis(f"claim_pouch_{pouch.id}_{user.id}")) for user in pouch.user.all()),
                "owner_id": pouch.user.id,
                "status": "OPEN" if pouch.expired_date > timezone.now() else "CLAIM",
                "time_end": pouch.expired_date.isoformat(),
                "opened": len(json.loads(get_from_redis(f"giveaway_pouch_{pouch.id}")).get("values_array", []))
            }
            response_data.append(pouch_data)

        for unopened_pouch in unopened_pouches:
            pouch_data = {
                "id": unopened_pouch['id'],
                "amount": unopened_pouch['amount'],
                "amount_claim": unopened_pouch['amount_claim'],
                "owner_id": unopened_pouch['owner_id'],
                "status": unopened_pouch['status'],
                "time_end": unopened_pouch['time_end'],
                "opened": unopened_pouch['opened']
            }
            response_data.append(pouch_data)

        response = {
            "statusCode": 200,
            "message": "Success",
            "data": response_data
        }
        return Response(response, status=status.HTTP_200_OK)
    

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
        wallet.sniff_coin += 100
        wallet.save()

        user_data = {
            "id": request.user.id,
            "name": f"{request.user.first_name} {request.user.last_name}",
            "wallet": wallet.user_wallet_id,
            "balance_sniff_coin": wallet.sniff_coin,
            "balance_sniff_point": wallet.sniff,
            "claim_expire": "2023-12-31T23:59:59Z",  # Example static date
            "createdCountPouch": 0,  # Example static value
            "createdCountPouchToday": 0,  # Example static value
            "level": {
                "send_envelope": 5  # Example static value
            }
        }

        return Response({"data":{"user": user_data}}, status=status.HTTP_200_OK)
