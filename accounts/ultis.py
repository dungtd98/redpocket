from django.core.cache import cache
from django.utils import timezone

def can_open_pouch(user):
    today = timezone.now().strftime('%Y-%m-%d')  # Lấy ngày hiện tại theo định dạng YYYY-MM-DD
    cache_key = f'open_pouch_{user.id}_{today}'  # Tạo khóa cache duy nhất cho mỗi người dùng mỗi ngày
    
    # Lấy số lần mở pouch trong ngày từ Redis
    open_count = cache.get(cache_key, 0)
    
    # Kiểm tra giới hạn
    if open_count < user.userprofile.daily_limit_open_pouch:
        # Tăng số lần mở pouch
        cache.incr(cache_key)
        
        # Đảm bảo khóa cache hết hạn sau 24 giờ (86400 giây)
        cache.expire(cache_key, 86400)
        
        return True  # Cho phép người dùng thực hiện hành động
    return False  # Đã đạt giới hạn, không cho phép thực hiện hành động


def can_share_pouch(user):
    today = timezone.now().strftime('%Y-%m-%d')  # Lấy ngày hiện tại
    cache_key = f'share_pouch_{user.id}_{today}'  # Tạo khóa cache duy nhất
    
    # Lấy số lần chia sẻ pouch trong ngày từ Redis
    share_count = cache.get(cache_key, 0)
    
    # Kiểm tra giới hạn
    if share_count < user.userprofile.daily_limit_share_pouch:
        # Tăng số lần chia sẻ pouch
        cache.incr(cache_key)
        
        # Đảm bảo khóa cache hết hạn sau 24 giờ
        cache.expire(cache_key, 86400)
        
        return True  # Cho phép người dùng thực hiện hành động
    return False  # Đã đạt giới hạn, không cho phép thực hiện hành động
 