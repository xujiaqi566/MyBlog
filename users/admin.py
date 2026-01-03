from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 使用装饰器注册 User 模型
@admin.register(User)
class MyUserAdmin(UserAdmin):
    # 找到 list_display，删除其中的 'bio'
    # 如果你想显示 bio，需要通过方法获取，或者干脆先去掉它
    list_display = ('username', 'email', 'is_staff', 'avatar')  # 去掉 'bio'

    # 同样检查 fieldsets，如果里面有 'bio' 也要去掉
    fieldsets = UserAdmin.fieldsets + (
        ('额外信息', {'fields': ('avatar',)}),  # 去掉 'bio'
    )