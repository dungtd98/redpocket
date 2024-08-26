from django.urls import path
from .views import GetUserProfileView, LeaderBoardView, TelegramAuthViewV1, index
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', GetUserProfileView.as_view(), name='get_user_profile'),
    path('leaderboard/', LeaderBoardView.as_view(), name='leaderboard'),
    path('telegram-auth/', TelegramAuthViewV1.as_view(), name='telegram_auth'),
    path('', index, name='index'),
]
