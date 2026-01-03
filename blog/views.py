import markdown
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # 导入装饰器
from .models import Post, Comment
from .forms import CommentForm

# 首页视图
def index(request):
    post_list = Post.objects.all().order_by('-created_time')
    return render(request, 'blog/index.html', {'post_list': post_list})

# 详情页视图
import markdown
from django.utils.safestring import mark_safe # 必须导入这个

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('blog:post_detail', pk=pk)
    else:
        form = CommentForm()

    # --- 重点修改区域 ---
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',  # 包含基础扩展
        'markdown.extensions.codehilite',  # 代码高亮
        'markdown.extensions.toc',  # 目录
        'markdown.extensions.nl2br',  # 回车即换行
    ])
    # 转换后使用 mark_safe，否则前端会直接显示 HTML 源码
    post.body = mark_safe(md.convert(post.body))
    # --------------------

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'form': form,
        'comments': comments
    })

# 点赞/取消点赞视图
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    # 多对多关系的判断与处理
    if user in comment.liked_by.all():
        comment.liked_by.remove(user)
    else:
        comment.liked_by.add(user)

    return redirect('blog:post_detail', pk=comment.post.pk)

# 删除评论视图
@login_required # 加上这个，确保 request.user 存在
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # 安全检查：只有本人可以删除
    if request.user == comment.user:
        comment.delete()

    return redirect('blog:post_detail', pk=comment.post.pk)


from django.contrib.auth.decorators import login_required
from .forms import PostForm


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # 自动将当前登录用户设为作者
            post.save()
            # 发布成功后跳转到文章详情页
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = PostForm()

    return render(request, 'blog/post_form.html', {'form': form})

from django.shortcuts import render, get_object_or_404
from .models import Post
from django.contrib.auth import get_user_model
User = get_user_model()
# 搜索用户功能
def user_search(request):
    query = request.GET.get('q')
    results = []
    if query:
        # 这里的 User 已经是 get_user_model() 返回的正确定制模型了
        results = User.objects.filter(username__icontains=query)
    return render(request, 'blog/user_search.html', {'results': results, 'query': query})
# 用户详细资料功能
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()


# blog/views.py
def user_profile(request, username):
    User = get_user_model()
    # 永远根据 URL 中的 username 查库，这保证了 profile_user 是固定的
    profile_user = get_object_or_404(User, username=username)

    # 这里的 user_posts 必须关联 profile_user
    user_posts = Post.objects.filter(author=profile_user).order_by('-created_time')

    return render(request, 'blog/user_profile.html', {
        'profile_user': profile_user,  # 被查看的博主
        'user_posts': user_posts
    })


from django.contrib import messages  # 用于显示删除成功的提示
@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # 权限检查：必须是作者本人
    if request.user == post.author:
        post.delete()
        messages.success(request, "文章删除成功！")
        return redirect('blog:index')
    else:
        messages.error(request, "你没有权限删除这篇文章。")
        return redirect('blog:post_detail', pk=pk)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post
from .forms import PostForm  # 假设你的表单类名是这个


@login_required
def post_edit(request, pk):
    # 获取要修改的文章
    post = get_object_or_404(Post, pk=pk)

    # 【权限检查】：如果当前用户不是作者，禁止编辑
    if request.user != post.author:
        return redirect('blog:post_detail', pk=pk)

    if request.method == "POST":
        # 用 POST 数据更新现有的 post 实例
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()  # author 不需要重新赋值，因为 instance 里已有
            return redirect('blog:post_detail', pk=post.pk)
    else:
        # GET 请求：用当前文章内容填充表单
        form = PostForm(instance=post)

    return render(request, 'blog/post_form.html', {
        'form': form,
        'is_edit': True,  # 告诉模板现在是“编辑”模式
        'post': post
    })