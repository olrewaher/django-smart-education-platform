from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.shortcuts import render
from django.utils.html import format_html
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, Category, CaseStudy, CaseChapter, Comment, Note, Favorite, BranchNode, BranchOption
# 引入你的模型
from .models import UserProfile, Category, CaseStudy, CaseChapter, Comment, Note, Favorite

# ==============================================================================
# 0. 全局后台配置
# ==============================================================================
admin.site.site_header = '思政案例库管理系统'
admin.site.site_title = '教学管理后台'
admin.site.index_title = '控制台'

# ==============================================================================
# 1. 用户管理模块 (核心权限改造)
# ==============================================================================
# 先注销原有的 User/Group，防止冲突
try:
    admin.site.unregister(Group)
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    权限分层用户管理：
    1. 超级管理员 (Superuser): 上帝视角，管理所有用户。
    2. 教师 (Staff): 只能查看、编辑、重置普通学生密码。看不到超管和其他教师。
    """
    list_display = ('username', 'first_name', 'email', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 🛡️ 教师只能看到普通学生 (非超管且非员工)
        return qs.filter(is_superuser=False, is_staff=False)

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if obj is None: return True
        # 🛡️ 严防下级修改上级：非超管不能修改超管账号
        if not request.user.is_superuser and obj.is_superuser:
            return False
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser and obj and obj.is_superuser:
            return False
        return request.user.is_superuser or request.user.is_staff

    def get_fieldsets(self, request, obj=None):
        # 如果是超管，显示完整字段
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)

        # 🛡️ 教师视图：隐藏权限字段，保留密码重置功能
        return (
            (None, {'fields': ('username', 'password')}),
            (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
            (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            (_('Permissions'), {'fields': ('is_active',)}),  # 只允许控制是否激活
        )

    def save_model(self, request, obj, form, change):
        # 🛡️ 教师创建的用户，强制锁定为普通用户
        if not request.user.is_superuser:
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)

        # 恢复并修改 changelist_view
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # 🔥 核心逻辑：把当前用户是不是超管（True/False）传给前端模板
        extra_context['is_superuser_flag'] = request.user.is_superuser

        # 组装 Django Admin 需要的默认上下文
        context = {
            **self.admin_site.each_context(request),
            **extra_context,
            'title': '用户与角色高级管理'
        }
        # 统一渲染你的 Vue 页面
        return render(request, 'admin/user_management.html', context)


# ==============================================================================
# 2. 核心业务：课程与章节管理
# ==============================================================================

class CaseChapterForm(forms.ModelForm):
    class Meta:
        model = CaseChapter
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attachment'].required = False
        self.fields['video_file'].required = False


class CaseChapterInline(admin.StackedInline):
    model = CaseChapter
    form = CaseChapterForm
    extra = 0
    min_num = 0
    can_delete = True

    class Media:
        js = ('js/admin_chapter_toggle.js',)

    fieldsets = (
        ('基础信息', {
            'fields': ('title', 'chapter_type', 'order'),
            'classes': ('wide',),
        }),
        ('📝 图文内容配置', {
            'fields': ('content_format', 'font_size', 'content_rich', 'content_md'),
            'description': '<div style="color:#666;">💡 提示：系统将根据选择的格式自动切换编辑器。</div>',
        }),
        ('📺 视频与课件', {
            'fields': ('video_file', 'video_url', 'attachment'),
            'classes': ('collapse',),
        }),
    )


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ('title_preview', 'category_label', 'author_info', 'chapter_stats', 'status_badge', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title',)
    list_per_page = 15
    autocomplete_fields = ['category']
    inlines = [CaseChapterInline]

    # --- 核心权限控制 ---

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 🛡️ 数据隔离：教师只能看到自己的课程
        return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        # 自动署名
        if not obj.pk and not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj and obj.author != request.user and not request.user.is_superuser:
            return False
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj and obj.author != request.user and not request.user.is_superuser:
            return False
        return request.user.is_staff or request.user.is_superuser

    # 🛡️ 安全补丁：防止外键下拉框泄露其他教师或超管账号
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            if not request.user.is_superuser:
                # 教师只能选自己（其实 save_model 会覆盖，但前端显示要安全）
                kwargs["queryset"] = User.objects.filter(pk=request.user.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # --- 显示辅助 ---

    @admin.display(description='案例标题', ordering='title')
    def title_preview(self, obj):
        return (obj.title[:20] + '...') if len(obj.title) > 20 else obj.title

    @admin.display(description='所属分类', ordering='category')
    def category_label(self, obj):
        return format_html(
            '<span style="background:#ecf5ff; color:#409EFF; padding:2px 5px; border-radius:4px;">{}</span>',
            obj.category.name) if obj.category else "-"

    @admin.display(description='章节概况')
    def chapter_stats(self, obj):
        count = obj.chapters.count()
        return f"共 {count} 节" if count > 0 else "暂无章节"

    @admin.display(description='发布教师', ordering='author')
    def author_info(self, obj):
        return obj.author.first_name or obj.author.username if obj.author else "—"

    @admin.display(description='热度', ordering='view_count')
    def status_badge(self, obj):
        views = getattr(obj, 'view_count', 0)
        return f"🔥 {views}" if views > 100 else f"🌱 {views}"


# ==============================================================================
# 3. 基础数据管理
# ==============================================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'case_count_display')
    search_fields = ('name',)

    @admin.display(description='关联案例数')
    def case_count_display(self, obj): return obj.casestudy_set.count()

    # 权限策略：教师可以“选”和“加”，但不能“改”和“删”（防止把别人的分类改坏了）
    def has_module_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser  # 仅限超管

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # 仅限超管


# ==============================================================================
# 4. 互动与数据中心
# ==============================================================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_case_title', 'content_preview', 'created_at')
    readonly_fields = ('user', 'case', 'content', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 🛡️ 教师只能管理【自己课程下】的评论
        return qs.filter(case__author=request.user)

    def has_module_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # 允许教师删除恶意评论
        return request.user.is_staff or request.user.is_superuser

    @admin.display(description='评论内容')
    def content_preview(self, obj): return (obj.content[:30] + '...') if len(obj.content) > 30 else obj.content

    @admin.display(description='所属案例', ordering='case__title')
    def get_case_title(self, obj): return obj.case.title


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """
    笔记管理：
    出于隐私保护，建议普通教师无法查看学生的私人笔记，除非业务强需求。
    此处配置为：超管可见所有，普通用户（在自己的前端）可见自己。
    后台仅对超管开放查看，防止教师窥探学生隐私。
    """
    list_display = ('user', 'case', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()  # 教师在后台不展示笔记，保护隐私

    def has_module_permission(self, request):
        return request.user.is_superuser  # 仅超管可见


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'case', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()  # 仅超管可见统计数据

    def has_module_permission(self, request):
        return request.user.is_superuser


# ==============================================================================
# 5. 视频交互节点管理 (图形化配置选项)
# ==============================================================================
class BranchOptionInline(admin.StackedInline):
    model = BranchOption
    extra = 2  # 默认留出两行给老师填 A/B 选项


@admin.register(BranchNode)
class BranchNodeAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'trigger_time', 'question')
    # 可以通过课程关联来过滤，方便老师查找
    list_filter = ('chapter__case',)
    inlines = [BranchOptionInline]

    # 🛡️ 权限隔离：老师只能看到自己课程的节点
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # 过滤出该教师名下的课程章节的节点
        return qs.filter(chapter__case__author=request.user)

    # 🛡️ 安全/体验优化：添加节点时，下拉框只显示属于该老师的“视频类型”章节
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "chapter" and not request.user.is_superuser:
            kwargs["queryset"] = CaseChapter.objects.filter(
                case__author=request.user,
                chapter_type='video'  # 只有视频才需要交互
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_module_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff or request.user.is_superuser