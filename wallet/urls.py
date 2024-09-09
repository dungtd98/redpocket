from django.urls import path
from .views import (CreateGiveawayPouchView, ClaimPouchTokenView, GetPouchListInfoView,
                     CreateStakeView, GetActiveStakeView, ClaimNewUserAPIView, ClaimStakeView)

urlpatterns = [
    path('coin-pouch/create', CreateGiveawayPouchView.as_view(), name='create_giveaway_pouch'),
    path('coin-pouch/open', ClaimPouchTokenView.as_view(), name='claim-pouch-token'),
    path('coin-pouch', GetPouchListInfoView.as_view(), name='get-pouch-list-info'),
    path('stakes', CreateStakeView.as_view(), name='create-stake'),
    path("stakes/claim", ClaimStakeView.as_view(), name='claim-pouch-token'),
    path('user/claim-new-user', ClaimNewUserAPIView.as_view(), name='claim-new-user'),
    path('stakes/me', GetActiveStakeView.as_view(), name='get-active-stake'),
    
]
