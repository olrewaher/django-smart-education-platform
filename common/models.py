from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field


# 1. 用户档案
class UserProfile(models.Model):
    USER_ROLES = (('admin', '普通管理员'), ('teacher', '教师'), ('student', '学生'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('角色', max_length=10, choices=USER_ROLES, default='student')
    student_id = models.CharField('学号/工号', max_length=20, blank=True)
    is_banned = models.BooleanField('是否封禁', default=False)
    ban_reason = models.CharField('封禁理由', max_length=255, blank=True, null=True)
    ban_end_time = models.DateTimeField('解封时间', blank=True, null=True)

    class Meta: verbose_name = '用户档案'; verbose_name_plural = verbose_name

    def __str__(self): return f"{self.user.username} ({self.get_role_display()})"


# 2. 分类
class Category(models.Model):
    name = models.CharField('分类名称', max_length=50)

    class Meta: verbose_name = '案例分类'; verbose_name_plural = verbose_name
    # 指定默认排序规则(按ID从小到大)
    ordering = ['id']
    def __str__(self): return self.name


# 3. 案例
class CaseStudy(models.Model):
    title = models.CharField('课程标题', max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="负责教师", related_name='cases', null=True,
                               blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='所属分类')
    description = models.TextField('课程简介', blank=True)
    cover_image = models.ImageField('封面图', upload_to='covers/', blank=True, null=True)
    view_count = models.PositiveIntegerField('浏览量', default=0)
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    content = models.TextField('导读/详情', blank=True)

    class Meta: verbose_name = '思政课程'; verbose_name_plural = verbose_name; ordering = ['-created_at']

    def __str__(self): return self.title


# 3.5 章节 (修复了 font_size 字段缺失问题)
class CaseChapter(models.Model):
    TYPE_CHOICES = (('video', '📺 视频学习'), ('text', '📄 图文阅读'), ('file', '💾 外部案例资料'))
    CONTENT_FORMATS = (('rich', '🌈 富文本'), ('md', '📝 Markdown'))
    FONT_SIZE_CHOICES = (('14px', '小号'), ('16px', '标准'), ('18px', '中号'), ('20px', '大号'))

    case = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, related_name='chapters', verbose_name="所属课程")
    title = models.CharField("章节标题", max_length=100)
    chapter_type = models.CharField("章节类型", max_length=10, choices=TYPE_CHOICES, default='video')

    # 🔥 确保这个字段存在
    content_format = models.CharField("排版模式", max_length=10, choices=CONTENT_FORMATS, default='rich')
    font_size = models.CharField("字体大小", max_length=10, choices=FONT_SIZE_CHOICES, default='16px')

    content_rich = CKEditor5Field("富文本编辑器", blank=True, null=True, config_name='default')
    content_md = models.TextField("Markdown编辑器", blank=True, null=True)
    video_file = models.FileField("视频文件", upload_to='videos/chapters/', blank=True)
    video_url = models.URLField("外部视频链接", blank=True)
    attachment = models.FileField("课件资料", upload_to='attachments/', blank=True)
    order = models.PositiveIntegerField("排序", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    resource_link = models.URLField(
        verbose_name="外部资料链接",
        blank=True,
        null=True,
        help_text="当选择【外部案例资料】时，可在此填入网盘或外部下载地址"
    )

    class Meta: verbose_name = "课程章节"; verbose_name_plural = verbose_name; ordering = ['order', 'created_at']

    def __str__(self): return f"[{self.get_chapter_type_display()}] {self.title}"


# 4. 评论 (添加了置顶字段)
class Comment(models.Model):
    case = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, related_name='comments', verbose_name="所属案例")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    content = models.TextField('评论内容')
    created_at = models.DateTimeField(auto_now_add=True)
    chapter = models.ForeignKey(CaseChapter, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='chapter_comments')

    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True, verbose_name="点赞用户")


    class Meta:
        verbose_name = '互动评论'
        verbose_name_plural = verbose_name

    def __str__(self): return f"{self.user.username}: {self.content[:20]}"

# 5. 笔记
class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    case = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    chapter = models.ForeignKey('CaseChapter', on_delete=models.SET_NULL, null=True, blank=True,verbose_name="所属章节")
    content = models.TextField('笔记内容')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: verbose_name = '学习笔记'; verbose_name_plural = verbose_name


# 6. 收藏
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    case = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: unique_together = ('user', 'case')


# 7. 学情数据统计
class StudyRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    case = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, verbose_name="所属课程", related_name='study_records')

    # 记录总秒数
    view_duration = models.PositiveIntegerField(default=0, verbose_name="学习时长(秒)")
    # 记录最后一次更新时间，方便统计“最近学习”
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")
    # 【新增】记录最后一次学习的章节
    last_chapter = models.ForeignKey(
        'CaseChapter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="最近学习章节"
    )
    class Meta:
        verbose_name = "学情记录"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'case')  # 保证一个用户对一个课程只有一条总记录

    def __str__(self):
        return f"{self.user.username} - {self.case.title} ({self.view_duration}s)"


# ==============================================================================
# 8. 视频分支交互模块 (高内聚：独立表结构，低耦合：外键挂载不影响原表)
# ==============================================================================
class BranchNode(models.Model):
    # 直接挂载到你现有的 CaseChapter 模型上
    chapter = models.ForeignKey(CaseChapter, on_delete=models.CASCADE, related_name='branch_nodes', verbose_name="所属视频章节")
    trigger_time = models.IntegerField(verbose_name="触发时间(秒)", help_text="例如：视频播放到第15秒弹出选项，填 15")
    question = models.CharField(max_length=255, verbose_name="弹出的问题")

    class Meta:
        verbose_name = '视频交互节点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.chapter.title} - {self.trigger_time}秒"

class BranchOption(models.Model):
    node = models.ForeignKey(BranchNode, on_delete=models.CASCADE, related_name='options', verbose_name="所属节点")
    text = models.CharField(max_length=100, verbose_name="选项文本", help_text="例如：选择A")
    feedback = models.TextField(verbose_name="选择后的解析/回答", help_text="学生选择该项后，弹出的反馈内容", blank=True, null=True)

    class Meta:
        verbose_name = '交互选项'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.text


# ==============================================================================
# 9. 消息通知模块 (新增)
# ==============================================================================
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="接收人")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="发送人")
    case = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, verbose_name="关联课程")
    content = models.CharField("通知内容", max_length=255)
    is_read = models.BooleanField("是否已读", default=False)
    created_at = models.DateTimeField("通知时间", auto_now_add=True)

    class Meta:
        verbose_name = '消息通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"发送给 {self.recipient.username} 的通知"


# ==============================================================================
# 10. 个人主页学习自动记录打卡日历模块
# ==============================================================================
from django.utils import timezone
class DailyStudyActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    date = models.DateField(default=timezone.localdate, verbose_name="学习日期")
    duration = models.PositiveIntegerField(default=0, verbose_name="每日学习总时长(秒)")

    class Meta:
        verbose_name = "每日学习活跃度"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.duration}s)"
