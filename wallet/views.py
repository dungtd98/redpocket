
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
    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = GiveawayPouchSerializer(data=data)
        can_share_pouch = check_can_share_pouch(request.user)
        if not can_share_pouch:
            return Response({"message": "You have reached the daily limit of opening pouch."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            pouch_sniff_coin = serializer.validated_data.get("amount")
            
            pouch_coin_array = divide_into_percentage_array(pouch_sniff_coin)
            serializer.save()
            redis_key_name = f"giveaway_pouch_{serializer.data.get('id')}"
            redis_value = json.dumps({
                "values_array": pouch_coin_array,
                "init_value": int(pouch_sniff_coin)
            })
            save_to_redis(redis_key_name, redis_value, 1800)
            add_tokens_to_user.apply_async(args=[request.user.id, serializer.data.get('id')], countdown=1800)
            
            response_data = {
                "status": "SUCCESS",
                "statusCode": 200,
                "data": {
                    "owner_id": serializer.data.get('user'),
                    "amount": serializer.data.get('amount'),
                    "time_end": (timezone.now() + timedelta(minutes=30)).isoformat(),
                    "id": serializer.data.get('id'),
                    "created_at": serializer.data.get('created_at'),
                    "updated_at": serializer.data.get('updated_at'),
                    "status": "OPENED"
                },
                "message": "CREATE_COIN_POUCH_SUCCESSFULLY"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ClaimPouchTokenView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Handles the HTTP POST request for opening a pouch.
        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            A Response object with the result of the pouch opening.
        """
        # Code implementation goes here
        can_open_pouch = check_can_open_pouch(request.user)
        if not can_open_pouch:
            return Response({"message": "You have reached the daily limit of opening pouch."}, status=status.HTTP_400_BAD_REQUEST)
        
        pouch_id = request.data.get('idCoinPouch')
        pouch = GiveawayPouch.objects.get(id=pouch_id)
        pouch_expired_date = pouch.expired_date
        
        if pouch_expired_date < timezone.now():
            return Response({"message": "This pouch has expired."}, status=status.HTTP_400_BAD_REQUEST)
        pouch_coin_value = json.loads(get_from_redis(f"giveaway_pouch_{pouch_id}"))
        pouch_coin_array = pouch_coin_value["values_array"]
        print(pouch_coin_array)
        if isinstance(pouch_coin_array, str):
            pouch_coin_array = json.loads(pouch_coin_array)
        coin_value, pouch_coin_array = get_random_value_from_array(pouch_coin_array)
        pouch_coin_value["values_array"] = pouch_coin_array
        save_to_redis(f"giveaway_pouch_{pouch_id}", json.dumps(pouch_coin_value), 86400)
        claim_value = {
            "id": timezone.now().timestamp(),
            "amount": coin_value,
            "amount_claim": coin_value,
            "amount_claim_view": coin_value,
            "owner_id": request.user.id,
            "status": "OPEN",
            "created_at": timezone.now().isoformat(),
            "updated_at": timezone.now().isoformat(),
            "histories_coin_pouchs": []
        }
        save_to_redis(f"claim_pouch_{pouch_id}_{request.user.id}", json.dumps(claim_value), 86400)
        return Response({"coin_value": coin_value}, status=status.HTTP_200_OK)


class GetPouchListInfoView(APIView):
    def get(self, request, *args, **kwargs):
        sent_pouches = GiveawayPouch.objects.filter(user=request.user)
        unopened_pouches = get_values_with_key_pattern(f"claim_pouch_*_{request.user.id}")
        print(type(unopened_pouches))
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
                "amount_claim_view": pouch.amount,  # Add this line
                "owner_id": pouch.user.id,
                "status": "OPEN" if pouch.expired_date > timezone.now() else "CLOSE",  # Update status to "CLOSE"
                "time_end": pouch.expired_date.isoformat(),
                "created_at": pouch.created_at.isoformat(),  # Add this line
                "updated_at": pouch.updated_at.isoformat(),  # Add this line
                "opened": len(values_array),
                "histories_coin_pouchs": []  # Add this line
            }
            response_data.append(pouch_data)

        for unopened_pouch in unopened_pouches:
            unopened_pouch = json.loads(unopened_pouch)
            pouch_data = {
                "id": unopened_pouch['id'],
                "amount": unopened_pouch['amount'],
                "amount_claim": unopened_pouch['amount_claim'],
                "amount_claim_view": unopened_pouch['amount'],  # Add this line
                "owner_id": unopened_pouch['owner_id'],
                "status": unopened_pouch['status'],
                "created_at": unopened_pouch['created_at'],  # Add this line
                "updated_at": unopened_pouch['updated_at'],  # Add this line
                "histories_coin_pouchs": []  # Add this line
            }
            response_data.append(pouch_data)

        response = {
            "status": "SUCCESS",
            "statusCode": 200,
            "message": "GET_COIN_POUCH_SUCCESSFULLY",
            "data": response_data
        }

        return Response(response, status=status.HTTP_200_OK)
    

class CreateStakeView(APIView):
    def post(self, request, *args, **kwargs):
        """
        API endpoint for creating a stake.

        Parameters:
        - request: The HTTP request object.
        - args: Additional positional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - If the serializer is valid, returns a response with the created stake data and a success message.
        - If the serializer is not valid, returns a response with the serializer errors and a bad request status.

        Example Usage:
        response = post(request, *args, **kwargs)
        """
        data = request.data.copy()
        data['user'] = request.user.id
        duration = data.get('duration', None)
        if not duration:
            return Response({"duration": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        data['end_time'] = timezone.now() + timedelta(days=duration)
        data['earning'] = 0
        serializer = UserStakeSerializer(data=data)
        if serializer.is_valid():
            stake = serializer.save()
            response_data = {
                "data": {
                    "amount_staked": stake.amount,
                    "created_at": stake.created_at.isoformat(),
                    "earnings": 0,
                    "end_time": stake.end_time.isoformat() if stake.end_time else None,
                    "end_time_stake": stake.end_time.isoformat(),
                    "id": stake.id,
                    "last_claim": stake.last_claim.isoformat() if stake.last_claim else None,
                    "start_time": stake.start_time.isoformat(),
                    "status": stake.status,
                    "updated_at": stake.updated_at.isoformat(),
                    "user_id": stake.user.id
                },
                "message": "Stake created successfully",
                "status": "SUCCESS",
                "statusCode": 201
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetActiveStakeView(APIView):
    def get(self, request, *args, **kwargs):
        active_stakes = UserStake.objects.get(user=request.user)
        serialized_data = UserStakeSerializer(active_stakes).data
        serialized_data["earnings"] = request.user.wallet.sniff_coin * 10
        response_data = {
            "data": serialized_data if serialized_data else None,
            "message": "Get info stake successfully",
            "status": "SUCCESS",
            "statusCode": 200
        }
        return Response(response_data, status=status.HTTP_200_OK)


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