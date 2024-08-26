from django.contrib import admin
from .models import Wallet, GiveawayPouch, UserStake, DailyStake, Task
# Register your models here.

admin.site.register(Wallet)
admin.site.register(GiveawayPouch)
admin.site.register(UserStake)
admin.site.register(DailyStake)
admin.site.register(Task)