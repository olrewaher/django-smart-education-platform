# ai_assistant/views.py
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from common.models import CaseStudy
from .services import EduAgent
from .utils import intent_router # 如果你有意图拦截模块，请取消注释
import json


def generate_stream(api_response):
    """流式输出标准化处理"""
    for chunk in api_response:
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            yield f"data: {json.dumps({'text': delta.content})}\n\n"


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    user_query = request.POST.get('query', '')
    course_id = request.POST.get('course_id', '')

    # 1. 意图拦截
    if intent_router(user_query) == "REFUSE":
        # 伪装成流式数据返回，前端打字机效果不会报错
        def refuse_stream():
            yield f"data: {json.dumps({'text': '检测到无效输入或无关话题。我是您的专属学习助手，请提问与当前课程案例相关的内容哦。'})}\n\n"

        return StreamingHttpResponse(
            refuse_stream(),
            content_type='text/event-stream'
        )

    # 2. 获取数据包
    try:
        case_obj = CaseStudy.objects.get(id=course_id)

        # 初始化拼接变量
        full_content = case_obj.content or ""
        is_video_case = False

        # --- 新增硬核逻辑：动态遍历后台真实的章节数据 ---
        # 获取该案例下的所有章节（假设你的外键 related_name 是默认的 casechapter_set）
        # 如果你在 models.py 里设置了 related_name='chapters'，请把下面改成 case_obj.chapters.all()
        chapters = case_obj.chapters.all()

        for chapter in chapters:
            # 只要有一个章节是视频，就打上视频标记
            if getattr(chapter, 'chapter_type', '') == 'video':
                is_video_case = True
            # 如果是图文章节，就把正文拼接起来喂给大模型
            elif getattr(chapter, 'chapter_type', '') == 'text' and getattr(chapter, 'content', ''):
                full_content += f"\n\n【章节：{chapter.title}】\n{chapter.content}"

        case_data = {
            "title": case_obj.title,
            "description": case_obj.description or "",
            "content": full_content.strip(),
            "is_video": is_video_case  # 将后台真实的类型标志传给大模型
        }

        # 3. 调用智能体
        answer_stream = EduAgent.ask(user_query, case_data=case_data)

        return StreamingHttpResponse(
            generate_stream(answer_stream),
            content_type='text/event-stream'
        )

    except CaseStudy.DoesNotExist:
        return JsonResponse({"answer": "找不到该案例，请检查链接。"})
    except Exception as e:
        print(f"System Error: {e}")
        return JsonResponse({"answer": "系统繁忙，请稍后再试。"})