import json
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.db.models import F
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import StudentRegistrationForm
from .utils import filter_service
from common.models import CaseStudy, StudyRecord
import re
import markdown
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
# ==============================================================================
# 一、页面视图
# ==============================================================================

# def index(request):
#     # 从 common.models 导入
#     from common.models import CaseStudy, Favorite
#     cases = CaseStudy.objects.all().order_by('-created_at')
#     fav_case_ids = set()
#     if request.user.is_authenticated:
#         fav_case_ids = set(Favorite.objects.filter(user=request.user).values_list('case_id', flat=True))
#     return render(request, 'student_web/index.html', {'cases': cases, 'fav_case_ids': fav_case_ids})


def index(request):
    # 1. 引入必要的模型
    # ⚠️ 变动点：新增导入 Category 和 Q
    from common.models import CaseStudy, Favorite, Category
    from django.db.models import Q

    # 2. 核心数据获取 (保持原有逻辑)
    cases = CaseStudy.objects.all().order_by('-created_at')

    # ⚠️ 变动点：新增获取分类列表 (为了让前端下拉框有选项)
    categories = Category.objects.all()

    # ==================================================
    # 3. 筛选逻辑 (这是新增的高内聚模块)
    # ==================================================
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')

    # 如果有搜索词，就过滤 cases
    if search_query:
        # icontains 表示忽略大小写模糊匹配
        cases = cases.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    # 如果选择了分类，就进一步过滤
    if category_id:
        cases = cases.filter(category_id=category_id)
    # ==================================================

    # 4. 收藏逻辑 (完全保留，未修改)
    fav_case_ids = set()
    if request.user.is_authenticated:
        fav_case_ids = set(Favorite.objects.filter(user=request.user).values_list('case_id', flat=True))

    # 5. 返回数据
    # ⚠️ 变动点：context 中多传了一个 categories
    context = {
        'cases': cases,
        'fav_case_ids': fav_case_ids,
        'categories': categories
    }
    return render(request, 'student_web/index.html', context)

def case_detail(request, case_id, chapter_id=None):
    # 从 common.models 导入
    from common.models import CaseStudy, Note, Comment, Favorite

    case = get_object_or_404(CaseStudy, pk=case_id)
    CaseStudy.objects.filter(pk=case_id).update(view_count=F('view_count') + 1)
    case.refresh_from_db()

    chapters = case.chapters.all()
    current_chapter = chapters.filter(id=chapter_id).first() if chapter_id else (
        chapters.first() if chapters.exists() else None)

    # ==================================================
    # 视频交互分支逻辑组装
    # ==================================================
    interactive_data = []
    # 只有当当前章节是视频，才去查询有没有交互节点配置
    if current_chapter and current_chapter.chapter_type == 'video':
        # prefetch_related 解决 N+1 查询问题，提升性能
        nodes = current_chapter.branch_nodes.prefetch_related('options').all()
        for node in nodes:
            interactive_data.append({
                "time": node.trigger_time,
                "question": node.question,
                "options": [{"text": opt.text, "feedback": opt.feedback} for opt in node.options.all()]
            })
    # ==================================================


    notes_data = []
    is_favorited = False
    if request.user.is_authenticated:
        notes_qs = Note.objects.filter(user=request.user, case=case).order_by('-created_at')
        notes_data = [{'id': n.id, 'content': n.content, 'created_at': n.created_at.strftime('%m-%d %H:%M')} for n in
                      notes_qs]
        is_favorited = Favorite.objects.filter(user=request.user, case=case).exists()

    comments_all = Comment.objects.select_related('user', 'chapter').filter(case=case).order_by('-created_at')
    paginator = Paginator(comments_all, 10)
    first_page = paginator.get_page(1)

    comments_data = [{
        'id': c.id,
        'user_id': c.user.id,
        'username': c.user.username,
        'avatar': c.user.username[0].upper() if c.user.username else 'U',
        'content': c.content,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
        'is_self': (request.user == c.user) if request.user.is_authenticated else False,
        'chapter_id': c.chapter.id if c.chapter else None,
        'chapter_title': c.chapter.title if c.chapter else '全案讨论',
        # 🔥 点赞数据正常返回
        'isLiked': (request.user in c.likes.all()) if request.user.is_authenticated else False,
        'likeCount': c.likes.count()
    } for c in first_page]

    context = {
        'case': case,
        'chapters': chapters,
        'current_chapter': current_chapter,
        'notes_json': json.dumps(notes_data),
        'comments_json': json.dumps(comments_data),
        'total_comments': comments_all.count(),
        'has_next': first_page.has_next(),
        'is_favorited': is_favorited,
        # 🌟 新增：将组装好的交互配置传给前端的 case_detail.html
        'interactive_config_json': json.dumps(interactive_data),
    }
    return render(request, 'student_web/case_detail.html', context)


def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "注册成功")
            return redirect('index')
    else:
        form = StudentRegistrationForm()
    return render(request, 'student_web/register.html', {'form': form})


# ==============================================================================
# 二、API 接口
# ==============================================================================

def _get_json_data(request):
    try:
        return json.loads(request.body)
    except:
        return {}


def api_get_comments(request, case_id):
    from common.models import Comment
    page_number = request.GET.get('page', 1)
    comments_qs = Comment.objects.select_related('user', 'chapter').filter(case_id=case_id).order_by('-created_at')
    page_obj = Paginator(comments_qs, 10).get_page(page_number)
    data = [{
        'id': c.id,
        'user_id': c.user.id,
        'username': c.user.username,
        'avatar': c.user.username[0].upper() if c.user.username else 'U',
        'content': c.content,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
        'is_self': (request.user == c.user) if request.user.is_authenticated else False,
        'chapter_id': c.chapter.id if c.chapter else None,
        'chapter_title': c.chapter.title if c.chapter else '全案讨论',
        'isLiked': (request.user in c.likes.all()) if request.user.is_authenticated else False,
        'likeCount': c.likes.count()
    } for c in page_obj]
    return JsonResponse({'status': 'success', 'data': data, 'has_next': page_obj.has_next()})


@login_required
@require_POST
def api_post_comment(request, case_id):
    from common.models import CaseStudy, CaseChapter, Comment,Notification
    from django.contrib.auth.models import User
    case = get_object_or_404(CaseStudy, pk=case_id)
    try:
        data = _get_json_data(request)
        content = data.get('content', '').strip()
        chapter_id = data.get('chapter_id')
        if not content: return JsonResponse({'status': 'error', 'message': '内容为空'}, status=400)

        is_sensitive, word = filter_service.check(content)
        if is_sensitive: return JsonResponse({'status': 'error', 'message': '含违规内容'})

        target_chapter = CaseChapter.objects.filter(pk=chapter_id).first() if chapter_id else None
        comment = Comment.objects.create(user=request.user, case=case, content=content, chapter=target_chapter)
        # ================================================================
        # 🌟 智能通知分发逻辑：解析是否是“楼中楼回复”
        # ================================================================
        match = re.match(r'^回复\s*@(.+?)\s*[:：]\s*(.*)$', content)
        if match:
            target_username = match.group(1)
            reply_text = match.group(2)  # 🌟 新增：提取出冒号后面的具体回复内容

            target_user = User.objects.filter(username=target_username).first()
            if target_user and target_user != request.user:
                Notification.objects.create(
                    recipient=target_user,
                    sender=request.user,
                    case=case,
                    # 🌟 修改：把具体的回复内容拼接到通知里面
                    content=f"在《{case.title}》中回复了你：“{reply_text}”"
                )


        return JsonResponse({
            'status': 'success',
            'data': {
                'id': comment.id,
                'user_id': request.user.id,
                'username': request.user.username,
                'avatar': request.user.username[0].upper(),
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_self': True,
                'chapter_id': target_chapter.id if target_chapter else None,
                'chapter_title': target_chapter.title if target_chapter else '全案讨论',
                'isLiked': False,
                'likeCount': 0
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': '系统错误'}, status=500)


@login_required
@require_POST
def api_post_note(request, case_id):
    from common.models import CaseStudy,CaseChapter, Note
    case = get_object_or_404(CaseStudy, pk=case_id)
    try:
        data = _get_json_data(request)
        content = data.get('content', '').strip()
        #获取前端传来的章节 ID
        chapter_id = data.get('chapter_id')
        target_chapter = CaseChapter.objects.filter(pk=chapter_id).first() if chapter_id else None

        if not content: return JsonResponse({'status': 'error'}, status=400)
        is_sensitive, word = filter_service.check(content)
        if is_sensitive: return JsonResponse({'status': 'error', 'message': '违规内容'})


        note = Note.objects.create(user=request.user, case=case,chapter=target_chapter, content=content)
        return JsonResponse({'status': 'success', 'data': {'id': note.id, 'content': note.content,
                                                           'created_at': note.created_at.strftime('%m-%d %H:%M')}})
    except:
        return JsonResponse({'status': 'error'}, status=500)


@login_required
@require_POST
def api_delete_note(request, note_id):
    from common.models import Note
    note = get_object_or_404(Note, pk=note_id)
    if request.user != note.user: return JsonResponse({'status': 'error'}, status=403)
    note.delete()
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def api_delete_comment(request, comment_id):
    from common.models import Comment
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user != comment.user: return JsonResponse({'status': 'error'}, status=403)
    comment.delete()
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def api_toggle_favorite(request, case_id):
    from common.models import CaseStudy, Favorite
    case = get_object_or_404(CaseStudy, pk=case_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, case=case)
    if not created:
        fav.delete()
        return JsonResponse({'status': 'success', 'action': 'removed'})
    return JsonResponse({'status': 'success', 'action': 'added'})


@login_required
def profile(request):
    # 多引入模型
    from common.models import Comment, Favorite, StudyRecord, Note,Notification
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('nickname', user.first_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        user.save()
        messages.success(request, '更新成功')
        return redirect('profile')

    study_records = StudyRecord.objects.select_related('case', 'case__category', 'last_chapter').filter(user=user).order_by('-last_updated')

    # 获取通知数据
    notifications = Notification.objects.filter(recipient=user)
    unread_count = notifications.filter(is_read=False).count()
    context = {
        'favorites': Favorite.objects.select_related('case').filter(user=user),
        'comments': Comment.objects.select_related('case').filter(user=user).order_by('-created_at'),
        'study_records': study_records,
        # 直接查询该用户的所有笔记，带上课程信息
        'notes': Note.objects.select_related('case','chapter').filter(user=user).order_by('-created_at'),
        # 传给前端的通知数据
        'notifications': notifications[:30],  # 最多只显示最近30条
        'unread_count': unread_count,

        'user': user,
        'computed_avatar': user.username[0].upper() if user.username else 'U'
    }
    return render(request, 'student_web/profile.html', context)


def get_active_users(request):
    if not request.session.session_key: request.session.save()
    CACHE_KEY = 'online_visitors_registry'
    registry = cache.get(CACHE_KEY, {})
    registry[request.session.session_key] = time.time()
    new_registry = {uid: ts for uid, ts in registry.items() if time.time() - ts < 300}
    cache.set(CACHE_KEY, new_registry, 300)
    return JsonResponse({'active_count': len(new_registry)})


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    # 从 common.models 导入 Comment
    from common.models import Comment
    try:
        comment = Comment.objects.get(id=comment_id)
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            is_liked = False
        else:
            comment.likes.add(request.user)
            is_liked = True
        return JsonResponse({'status': 'success', 'is_liked': is_liked, 'like_count': comment.likes.count()})
    except Comment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '评论不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



#学生端视图，接收前端发来的“心跳包”
@login_required
@require_POST
def update_study_duration(request):
    """
    接收前端的心跳包，累加学习时长
    """
    try:
        data = json.loads(request.body)
        case_id = data.get('case_id')
        duration = int(data.get('duration', 10))  # 默认每次心跳代表10秒

        #获取前端传来的章节ID
        chapter_id = data.get('chapter_id')
        # 1. 找到对应的课程
        case = CaseStudy.objects.get(id=case_id)

        # 2. 获取或创建学情记录
        # get_or_create 会返回两个值：对象(record) 和 是否新创建(created)
        record, created = StudyRecord.objects.get_or_create(
            user=request.user,
            case=case
        )

        # 3. 累加时长 (单位：秒)
        record.view_duration += duration


        # 如果有章节ID，就更新进去
        if chapter_id:
            record.last_chapter_id = chapter_id
        record.save()

        # ==================================================
        # 🌟 日历打卡：同步累加今天的总时长
        # ==================================================
        from django.utils import timezone
        from common.models import DailyStudyActivity
        today = timezone.localdate()
        daily_record, _ = DailyStudyActivity.objects.get_or_create(user=request.user, date=today)
        daily_record.duration += duration
        daily_record.save()
        # ==================================================

        return JsonResponse({'status': 'success', 'total_duration': record.view_duration})

    except CaseStudy.DoesNotExist:
        return JsonResponse({'status': 'error', 'msg': '课程不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)

@login_required
@require_POST
def api_read_notifications(request):
    """一键将所有未读消息标为已读"""
    from common.models import Notification
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required
def export_notes(request):
    """将用户的笔记导出为精美的独立 HTML 网页文件"""
    from common.models import Note

    notes = Note.objects.select_related('case', 'chapter').filter(user=request.user).order_by('-created_at')

    # 1. 先拼接 Markdown 格式的纯文本
    lines = [f"# {request.user.username} 的专属学习笔记\n\n"]
    lines.append(f"> 导出时间：{timezone.now().strftime('%Y-%m-%d %H:%M')}\n> 共计 {notes.count()} 条笔记\n\n---\n\n")

    for note in notes:
        title = f"{note.case.title} / {note.chapter.title}" if note.chapter else f"{note.case.title}"
        lines.append(f"### 📚 {title}\n")
        lines.append(f"**记录时间:** {note.created_at.strftime('%Y-%m-%d %H:%M')}\n\n")
        lines.append(f"{note.content}\n\n")
        lines.append("---\n\n")

    md_content = "".join(lines)

    # 2. 将 Markdown 转换为 HTML 标签
    html_body = markdown.markdown(md_content)

    # 3. 注入 CSS 样式，打造排版（仿照现代笔记软件）
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{request.user.username} 的学习笔记</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
                line-height: 1.8;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #f9fafb;
            }}
            .container {{
                background: #ffffff;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            }}
            h1 {{ color: #00aeec; border-bottom: 2px solid #eef2f5; padding-bottom: 15px; margin-bottom: 30px; }}
            h3 {{ color: #2c3e50; margin-top: 40px; display: flex; align-items: center; }}
            blockquote {{ 
                color: #666; border-left: 4px solid #00aeec; 
                padding: 10px 15px; background: #f0f7ff; 
                border-radius: 0 8px 8px 0; margin: 0 0 20px 0;
            }}
            hr {{ border: 0; border-top: 1px dashed #e3e5e7; margin: 30px 0; }}
            p {{ margin-bottom: 15px; font-size: 15px; }}
            strong {{ color: #00aeec; }}
        </style>
    </head>
    <body>
        <div class="container">
            {html_body}
        </div>
    </body>
    </html>
    """

    # 4. 返回 HTML 文件流
    response = HttpResponse(html_template, content_type='text/html; charset=utf-8')
    # 文件后缀改为 .html
    response['Content-Disposition'] = f'attachment; filename="StudyNotes_{request.user.username}.html"'

    return response



#某年某月自动打卡数据API
@login_required
def api_get_study_calendar(request):
    """获取指定月份的打卡日历数据"""
    from common.models import DailyStudyActivity
    from django.utils import timezone

    # 获取前端传来的年月，默认是当月
    try:
        year = int(request.GET.get('year', timezone.localdate().year))
        month = int(request.GET.get('month', timezone.localdate().month))
    except ValueError:
        return JsonResponse({'status': 'error', 'message': '参数错误'}, status=400)

    # 核心业务规则：只有学习时长 >= 1800 秒（30分钟）才算签到
    activities = DailyStudyActivity.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month,
        duration__gte=1800
    )

    # 提取达标的具体日期（比如 [1, 5, 12, 16]）
    checked_in_days = [act.date.day for act in activities]

    return JsonResponse({
        'status': 'success',
        'year': year,
        'month': month,
        'checked_in_days': checked_in_days
    })
