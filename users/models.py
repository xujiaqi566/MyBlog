from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. 自定义用户模型
class User(AbstractUser):
    # 系统内置的头像选项
    AVATAR_CHOICES = [
        ('avatars/default.png', '默认头像'),
        ('avatars/avatar1.png', '看书'),
        ('avatars/avatar2.png', '发呆'),
        ('avatars/avatar3.png', '下雨'),
        ('avatars/avatar4.png', '钓鱼'),
        ('avatars/avatar5.png', '傻乐'),
        ('avatars/avatar6.png', '睡着'),
        ('avatars/avatar7.png', '装可爱'),
    ]

    # 头像存储为字符串路径
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # 关注功能逻辑
    following = models.ManyToManyField(
        'self',
        through='Contact',
        related_name='followers',
        symmetrical=False
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

# 2. 关注关系中间表
class Contact(models.Model):
    user_from = models.ForeignKey(User, related_name='rel_from_set', on_delete=models.CASCADE)
    user_to = models.ForeignKey(User, related_name='rel_to_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, verbose_name="关注时间")

    class Meta:
        ordering = ('-created',)
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'{self.user_from} 关注了 {self.user_to}'

# 3. 用户扩展资料 (仅保留 bio，头像统一使用 User.avatar)
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    # 删除了这里的 avatar，防止与 User 冲突
    bio = models.TextField(max_length=500, blank=True, verbose_name="个人简介")

    def __str__(self):
        return f"{self.user.username} 的个人资料"

# 4. 私信模型
class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE, verbose_name="发送者")
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, verbose_name="接收者")
    content = models.TextField(verbose_name="内容")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")

    class Meta:
        ordering = ('timestamp',)
        verbose_name = "私信"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.sender} 对 {self.recipient} 说: {self.content[:20]}'

# 5. 通知模型
class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verb = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

# 6. 信号 (Signals) - 自动创建/保存 Profile
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    instance.profile.save()