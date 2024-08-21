from django.urls import path
from .views import CreateGiveawayPouchView

urlpatterns = [
    path('create-giveaway-pouch', CreateGiveawayPouchView.as_view(), name='create-giveaway-pouch'),
]
