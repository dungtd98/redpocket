from django.urls import path
from .views import CreateGiveawayPouchView, ClaimPouchTokenView, GetPouchListInfoView, CreateStakeView, GetActiveStakeView

urlpatterns = [
    path('create-giveaway-pouch', CreateGiveawayPouchView.as_view(), name='create-giveaway-pouch'),
    path('claim-pouch-token', ClaimPouchTokenView.as_view(), name='claim-pouch-token'),
    path('get-pouch-list-info', GetPouchListInfoView.as_view(), name='get-pouch-list-info'),
    path('create-stake', CreateStakeView.as_view(), name='create-stake'),
    path('get-active-stake', GetActiveStakeView.as_view(), name='get-active-stake'),
    
]
