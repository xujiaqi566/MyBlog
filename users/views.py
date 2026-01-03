from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages

# 导入你自己的模型和表单
from .models import Profile, Notification, Message, Contact
from .forms import UserProfileForm, RegisterForm

# 获取当前项目激活的用户模型
User = get_user_model()


# --- 辅助函数：获取全局未读计数 ---
def get_common_context(user):
    if user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        unread_messages = Message.objects.filter(recipient=user, is_read=False).count()
        return {
            'total_unread_count': unread_notifications + unread_messages,
            'unread_notifications_count': unread_notifications,
            'unread_messages_count': unread_messages,
        }
    return {}


# 1. 个人中心主页 (整合了 profile 和 profile_view)
def profile_view(request, username):
    """
    显示个人主页，支持查看自己和他人的主页
    """
    # 1. 获取目标用户（即 URL 里的那个用户）
    target_user = get_object_or_404(User, username=username)

    # 2. 获取该用户的文章 (默认使用 post_set，除非你在 Post 模型里改了 related_name)
    user_posts = target_user.post_set.all().order_by('-created_time')

    # 3. 获取通用上下文（未读消息数等）
    context = get_common_context(request.user)

    # 4. 合并所有数据传给模板
    context.update({
        'profile_user': target_user,
        'user_posts': user_posts,
    })

    return render(request, 'users/user_profile.html', context)


# 2. 编辑个人资料
@login_required
def edit_profile(request):
    """
    编辑当前登录用户的资料
    """
    if request.method == 'POST':
        # 必须确保有 request.FILES 才能接收图片
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # 保存 User 模型基础字段 (username, email, avatar)
            user = form.save()

            # 同步保存 Profile 模型的 bio (个人简介)
            profile, created = Profile.objects.get_or_create(user=user)
            profile.bio = form.cleaned_data.get('bio')
            profile.save()

            messages.success(request, "个人资料更新成功！")
            # 关键修复：保存后跳转到个人主页视图，并带上当前用户的 username
            return redirect('users:profile', username=user.username)
    else:
        # 初始数据加载
        initial_data = {}
        if hasattr(request.user, 'profile'):
            initial_data['bio'] = request.user.profile.bio
        form = UserProfileForm(instance=request.user, initial=initial_data)

    return render(request, 'users/edit_profile.html', {'form': form})


# 3. 用户注册
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


# 4. 关注/取关逻辑
@login_required
@require_POST
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            target_user = User.objects.get(id=user_id)
            if action == 'follow':
                _, created = Contact.objects.get_or_create(
                    user_from=request.user,
                    user_to=target_user
                )
                if created:
                    # 产生新关注通知
                    Notification.objects.create(
                        sender=request.user,
                        recipient=target_user,
                        verb='follow'
                    )
            else:
                Contact.objects.filter(
                    user_from=request.user,
                    user_to=target_user
                ).delete()
            return JsonResponse({'status': 'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})


# 5. 聊天详情页
@login_required
def chat_detail(request, username):
    recipient = get_object_or_404(User, username=username)

    # 简易互关判断逻辑 (假设 Contact 模型建立了 following 关联)
    # 这里根据你的模型结构，通常需要判断双方是否存在 Contact 记录
    is_following = Contact.objects.filter(user_from=request.user, user_to=recipient).exists()
    is_followed = Contact.objects.filter(user_from=recipient, user_to=request.user).exists()

    if not (is_following and is_followed):
        return render(request, 'users/chat_error.html', {'message': '只有互相关注后才能聊天哦！'})

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(sender=request.user, recipient=recipient, content=content)
            return redirect('users:chat_detail', username=username)

    messages_query = Message.objects.filter(
        Q(sender=request.user, recipient=recipient) |
        Q(sender=recipient, recipient=request.user)
    ).order_by('timestamp')

    # 标记已读
    messages_query.filter(recipient=request.user, is_read=False).update(is_read=True)

    context = {
        'recipient': recipient,
        'chat_messages': messages_query
    }
    context.update(get_common_context(request.user))
    return render(request, 'users/chat_detail.html', context)


# 6. 会话列表（互关好友）
@login_required
def chat_list(request):
    """
    显示与当前用户互关的好友列表
    """
    # 1. 找到我关注的所有人
    # 注意：这里我们查询 Contact 模型，user_from 是我自己
    i_follow = Contact.objects.filter(user_from=request.user).values_list('user_to', flat=True)

    # 2. 在这些我关注的人中，筛选出那些也关注了我的人
    # 即：查找 Contact 记录，其中 user_from 是对方，user_to 是我自己
    friends_ids = Contact.objects.filter(
        user_from_id__in=i_follow,
        user_to=request.user
    ).values_list('user_from', flat=True)

    # 3. 获取这些好友的 User 对象
    friends = User.objects.filter(id__in=friends_ids)

    context = {
        'friends': friends,
    }
    # 更新未读计数
    context.update(get_common_context(request.user))
    return render(request, 'users/chat_list.html', context)

# 7. 通知列表
@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')

    # 标记已读
    notifications.filter(is_read=False).update(is_read=True)

    context = {
        'notifications': notifications
    }
    context.update(get_common_context(request.user))
    return render(request, 'users/notifications.html', context)