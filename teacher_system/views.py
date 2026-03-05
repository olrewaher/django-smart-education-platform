import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from common.models import UserProfile,StudyRecord,CaseStudy,Comment, Note, Favorite
from datetime import timedelta,date
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.db.models import Sum, Count, F
import json

# 👑 权限计算器
def get_user_level(user):
    if not user.is_authenticated: return -1
    if user.is_superuser: return 100  # Level 100: 上帝
    if hasattr(user, 'profile'):
        role = user.profile.role
        if role == 'admin': return 50  # Level 50: 普管
        if role == 'teacher': return 10  # Level 10: 教师
    return 0  # Level 0: 学生


# 1. 获取列表
@login_required
def get_user_list_api(request):
    current_level = get_user_level(request.user)
    if current_level < 10: return JsonResponse({'code': 403, 'msg': '权限不足'})

    keyword = request.GET.get('keyword', '').strip()

    # --- 🔥 核心安全补丁开始：根据权限级别隔离数据 ---
    # 基础查询集
    users_query = User.objects.select_related('profile').all().order_by('-date_joined')

    if current_level < 100:
        # 如果不是超级管理员 (Level < 100)，绝对不能看到超管账号
        users_query = users_query.filter(is_superuser=False)

        if current_level < 50:
            # 如果只是普通教师 (Level < 50)，他只能看到学生 (Level=0)
            # 排除掉 profile.role 是 'admin' 或 'teacher' 的用户
            users_query = users_query.exclude(profile__role__in=['admin', 'teacher'])

            # 补充防线：确保即使没有 profile 或者是 staff 的用户也过滤掉
            users_query = users_query.filter(is_staff=False)
            # --- 🔥 核心安全补丁结束 ---

    # 应用搜索关键字
    if keyword:
        users_query = users_query.filter(
            Q(username__icontains=keyword) | Q(profile__student_id__icontains=keyword) | Q(email__icontains=keyword)
        )

    data_list = []
    # 使用过滤后的 users_query 循环
    for u in users_query:
        profile = getattr(u, 'profile', None)

        # 角色判定
        if u.is_superuser:
            role = 'superuser'
        elif profile and profile.role == 'admin':
            role = 'admin'
        elif profile and profile.role == 'teacher':
            role = 'teacher'
        else:
            role = 'student'

        real_name = profile.student_id if profile else '无数据'

        # 封禁判定
        is_banned = False
        ban_reason = ''
        ban_end_time = ''
        if profile and profile.is_banned:
            is_banned = True
            if profile.ban_end_time and timezone.now() > profile.ban_end_time:
                is_banned = False
            else:
                ban_reason = profile.ban_reason
                ban_end_time = profile.ban_end_time.strftime('%Y-%m-%d %H:%M') if profile.ban_end_time else '永久'

        # 权限压制计算
        can_edit = current_level > get_user_level(u)

        data_list.append({
            'id': u.id,
            'username': u.username,
            'realName': real_name,
            'email': u.email,
            'role': role,
            'status': 'banned' if is_banned else 'active',
            'banReason': ban_reason,
            'banEndTime': ban_end_time,
            'dateJoined': u.date_joined.strftime('%Y-%m-%d'),
            'canEdit': can_edit
        })

    return JsonResponse({'code': 200, 'data': data_list, 'meta': {'currentUserLevel': current_level}})


# 2. 封禁/解封
@login_required
def user_action_api(request):
    if request.method != 'POST': return JsonResponse({'code': 405, 'msg': 'Method Error'})
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        action = data.get('action')

        target_user = User.objects.get(id=user_id)
        if get_user_level(request.user) <= get_user_level(target_user):
            return JsonResponse({'code': 403, 'msg': '权限不足：无法操作同级或上级'})

        if not hasattr(target_user, 'profile'): return JsonResponse({'code': 404, 'msg': '档案缺失'})
        profile = target_user.profile

        if action == 'ban':
            profile.is_banned = True
            profile.ban_reason = data.get('reason')
            profile.ban_end_time = data.get('endTime') if data.get('banType') == 'temp' else None
            profile.save()
        elif action == 'unlock':
            profile.is_banned = False
            profile.ban_reason = None
            profile.ban_end_time = None
            profile.save()

        return JsonResponse({'code': 200, 'msg': '操作成功'})
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': str(e)})


# 3. 新增用户
@login_required
def add_user_api(request):
    if request.method != 'POST': return JsonResponse({'code': 405, 'msg': 'Method Error'})
    try:
        data = json.loads(request.body)
        username, password = data.get('username'), data.get('password')
        role, real_name, email = data.get('role', 'student'), data.get('realName', ''), data.get('email', '')

        if not username or not password: return JsonResponse({'code': 400, 'msg': '必填项为空'})
        if User.objects.filter(username=username).exists(): return JsonResponse({'code': 400, 'msg': '用户已存在'})

        # 权限校验
        cur_level = get_user_level(request.user)
        if role == 'admin' and cur_level < 100: return JsonResponse({'code': 403, 'msg': '只有超管可创建管理员'})
        if role == 'teacher' and cur_level < 50: return JsonResponse({'code': 403, 'msg': '权限不足'})

        new_user = User.objects.create_user(username=username, password=password, email=email)

        # 权限分配
        new_user.is_staff = (role in ['admin', 'teacher'])
        new_user.is_superuser = False  # 永远不通过接口创建超管
        new_user.save()

        UserProfile.objects.create(user=new_user, role=role, student_id=real_name)
        return JsonResponse({'code': 200, 'msg': '创建成功'})
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': str(e)})


# 4. 编辑用户 (加入提权/降级功能)
@login_required
def edit_user_api(request):
    if request.method != 'POST': return JsonResponse({'code': 405, 'msg': 'Method Error'})
    try:
        data = json.loads(request.body)
        target = User.objects.get(id=data.get('userId'))
        cur_level = get_user_level(request.user)

        # 1. 基础权限校验：不能编辑同级或上级
        if cur_level <= get_user_level(target):
            return JsonResponse({'code': 403, 'msg': '权限不足：无法编辑同级或上级'})

        # 2. 更新基础信息
        if data.get('email') is not None: target.email = data.get('email')
        if data.get('password'): target.set_password(data.get('password'))

        # 3. 处理提权/降级逻辑 (核心安全区)
        new_role = data.get('role')
        if new_role and hasattr(target, 'profile'):
            # 安全校验：当前操作者是否有资格赋予这个新角色？
            if new_role == 'admin' and cur_level < 100:
                return JsonResponse({'code': 403, 'msg': '越权拦截：只有超管可以任命普通管理员'})
            if new_role == 'teacher' and cur_level < 50:
                return JsonResponse({'code': 403, 'msg': '越权拦截：只有管理员以上可以任命教师'})

            # 更新 Profile 表的业务角色
            target.profile.role = new_role
            target.profile.student_id = data.get('realName')
            target.profile.save()

            # 同步更新 Django 底层的 is_staff 权限（决定能不能进 Admin 后台）
            if new_role in ['admin', 'teacher']:
                target.is_staff = True
            else:
                target.is_staff = False  # 如果被降级为学生，撤销后台登录权限

        target.save()

        return JsonResponse({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': str(e)})

# 5. 获取图表数据
@login_required
def case_analytics(request):
    # ================= 1. 课程热度分析 (柱状图) =================
    cases = CaseStudy.objects.annotate(
        total_duration=Sum('study_records__view_duration'),
        interaction_total=Count('comments') + Count('favorite')  # 综合互动数
    ).values('title', 'total_duration', 'interaction_total').order_by('-total_duration')[:10]

    chart_labels = [c['title'] for c in cases]
    chart_data_duration = [round((c['total_duration'] or 0) / 60, 1) for c in cases]
    chart_data_interaction = [c['interaction_total'] for c in cases]

    # ================= 2. 学习行为热力图  =================
    # 获取当前带时区的精确时间
    now = timezone.now()
    one_year_ago = now - timedelta(days=365)

    # 传给 ECharts 依然只需要纯日期字符串格式，所以用 .date() 转换一下
    heatmap_range = [str(one_year_ago.date()), str(now.date())]

    # 获取每天的评论数量（此时用带时区的 one_year_ago 去过滤就不会报警告了）
    daily_activity = Comment.objects.filter(created_at__gte=one_year_ago) \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')

    # 格式化为 ECharts Heatmap 需要的格式: [['2023-01-01', 5], ...]
    heatmap_data = [[str(item['date']), item['count']] for item in daily_activity]

    # ================= 3. “学生学习数据”多维雷达图 (五维数据) =================
    # 获取最活跃的 top 5 学生，分析他们的各项指标
    top_students_qs = StudyRecord.objects.filter(
        user__profile__role='student'
    ).values('user__username', 'user__id').annotate(
        total_time=Sum('view_duration')
    ).order_by('-total_time')[:5]

    radar_indicators = [
        {'name': '学习时长', 'max': 300},  # 假设满分基准，根据实际调整
        {'name': '评论互动', 'max': 20},
        {'name': '记笔记', 'max': 10},
        {'name': '收藏', 'max': 10},
        {'name': '点赞', 'max': 20}
    ]

    radar_series = []
    student_list_table = []  # 顺便给表格用

    for s in top_students_qs:
        uid = s['user__id']
        username = s['user__username']

        # 查询各维度数据
        duration_min = round(s['total_time'] / 60, 1)
        comment_count = Comment.objects.filter(user_id=uid).count()
        note_count = Note.objects.filter(user_id=uid).count()
        fav_count = Favorite.objects.filter(user_id=uid).count()
        # 假设有点赞记录表，如果没有可暂填0
        like_count = 0

        # 雷达图数据
        radar_series.append({
            'value': [duration_min, comment_count, note_count, fav_count, like_count],
            'name': username
        })

        # 表格数据
        student_list_table.append({
            'name': username,
            'duration': f"{duration_min} 分",
            'score': comment_count * 2 + note_count * 5 + duration_min * 0.5  # 简单计算一个活跃分
        })

    context = {
        'chart_labels': json.dumps(chart_labels, ensure_ascii=False),
        'chart_data_duration': json.dumps(chart_data_duration),
        'chart_data_interaction': json.dumps(chart_data_interaction),
        'heatmap_data': json.dumps(heatmap_data),
        'heatmap_range': json.dumps(heatmap_range),  # <--- 新增这个变量传给前端
        'radar_data': json.dumps(radar_series, ensure_ascii=False),
        'student_list': student_list_table,
    }

    return render(request, 'teacher_system/analytics.html', context)