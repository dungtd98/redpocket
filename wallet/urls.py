from django.urls import path
from .views import CreateGiveawayPouchView, ClaimPouchTokenView, GetPouchListInfoView, CreateStakeView, GetActiveStakeView

urlpatterns = [
    path('coin-pouch/create', CreateGiveawayPouchView.as_view(), name='create-giveaway-pouch'),
    path('coin-pouch/claim', ClaimPouchTokenView.as_view(), name='claim-pouch-token'),
    path('coin-pouch', GetPouchListInfoView.as_view(), name='get-pouch-list-info'),
    path('create-stake', CreateStakeView.as_view(), name='create-stake'),
    path('get-active-stake', GetActiveStakeView.as_view(), name='get-active-stake'),
    
]
