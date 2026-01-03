from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # 后台列表页显示的列
    list_display = ('title', 'author', 'created_time', 'modified_time')
    # 搜索框支持按标题和正文搜索
    search_fields = ('title', 'body')
    # 过滤器支持按时间筛选
    list_filter = ('created_time', 'author')