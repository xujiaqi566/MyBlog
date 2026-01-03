from django.db import models
from django.conf import settings  # 用于引用自定义用户模型


class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="标题")
    body = models.TextField(verbose_name="正文")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    modified_time = models.DateTimeField(auto_now=True, verbose_name="修改时间")

    # 外键关联：一篇文章只有一个作者，一个作者可以写多篇文章
    # 当用户被删除时，其文章也会被级联删除 (models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="作者")

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']  # 按创建时间倒序排列

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    body = models.TextField("评论内容")
    created_time = models.DateTimeField(auto_now_add=True)
    # 这一行 Django 会自动在数据库生成 blog_comment_liked_by 表
    liked_by = models.ManyToManyField('users.User', related_name='liked_comments', blank=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.user.username} 对 {self.post.title} 的评论"