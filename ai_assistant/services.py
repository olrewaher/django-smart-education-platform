# ai_assistant/services.py
from openai import OpenAI
from django.conf import settings
import re

client = OpenAI(
    api_key=settings.VOLCENGINE_API_KEY,  # 确保 settings.py 变量名一致
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)


class EduAgent:
    # 通用人设
    SYSTEM_PROMPT = """你名为"智学助教"，是智慧在线教育Web系统的 AI 助教。
    请基于提供的【上下文信息】回答问题。
    严禁回答与课程无关的问题。
    """

    @staticmethod
    def _get_best_chunks(query, full_text, top_k=3):
        """保留非常有用的内存切片检索算法"""
        if not full_text: return ""
        chunks = [p.strip() for p in re.split(r'\n+|。', full_text) if len(p.strip()) > 10]
        if not chunks: return full_text[:800]

        chunk_scores = []
        for chunk in chunks:
            score = sum(1 for char in query if char in chunk)
            chunk_scores.append((score, chunk))

        chunk_scores.sort(key=lambda x: x[0], reverse=True)
        best_chunks = [chunk for score, chunk in chunk_scores[:top_k] if score > 0]

        if not best_chunks: return chunks[0] if chunks else ""
        return "\n...\n".join(best_chunks)

    @classmethod
    def ask(cls, question, chat_history=None, case_data=None):
        case_data = case_data or {}
        title = case_data.get("title", "未知案例")
        desc = case_data.get("description", "")
        content = case_data.get("content", "")
        is_video = case_data.get("is_video", False)  # 接收后端传来的真实标志
        # === 核心逻辑：智能模式切换 ===

        # 1. 判断是否有足够的文本内容 (比如超过50个字)
        if len(content) > 50:
            # 【模式 A：文本 RAG 模式】
            # 使用你的切片算法，从长文中提取精华
            relevant_text = cls._get_best_chunks(question, content)

            context_prompt = (
                f"【当前学习案例】{title}\n"
                f"【简介】{desc}\n"
                f"【相关正文片段】(已过滤无关内容):\n"
                f"{relevant_text}\n"
                f"----------------\n"
                f"【指令】请优先基于上述片段回答。如果片段信息不足，可适当补充。"
            )
        elif is_video:
            # 【模式 B：视频/元数据模式】
            # 没有正文，利用标题激活 AI 的内部知识库
            # 后台明确查出这是一个视频课程，且没有匹配到长文本
            context_prompt = (
                f"【当前学习场景】用户正在观看视频课程《{title}》\n"
                f"【视频简介】{desc}\n"
                f"----------------\n"
                f"【指令】当前为视频课程暂无配套文本。请你作为专业教师，"
                f"利用你的知识库，围绕《{title}》这一主题为用户答疑解惑。"
            )
        else:
        # 【模式 C：通用兜底模式】
        # 既不是视频，也没拿到长文本（可能是纯大纲页）
            context_prompt = (
                f"【当前学习案例】《{title}》\n"
                f"【简介】{desc}\n"
                f"----------------\n"
                f"【指令】请你作为深谙课程思政与计算机的专业教师，利用内置知识库为用户解答。"
            )

        # 组装消息
        messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]
        messages.append({"role": "system", "content": context_prompt})

        if chat_history:
            messages.extend(chat_history[-2:])

        messages.append({"role": "user", "content": question})

        try:
            response = client.chat.completions.create(
                model=settings.VOLCENGINE_MODEL_EP,
                messages=messages,
                stream=True,
                temperature=0.7  # 稍微增加一点灵活性，适应纯视频模式
            )
            return response
        except Exception as e:
            print(f"API Error: {e}")

            # 返回一个生成器，抛出错误信息给前端
            def error_generator():
                yield type('obj', (object,), {'choices': [type('obj', (object,), {
                    'delta': type('obj', (object,), {'content': 'AI 服务暂时不可用，请检查后台配置。'})})]})

            return error_generator()