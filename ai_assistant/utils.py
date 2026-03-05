def intent_router(user_input):
    """
    低成本过滤：在发给 AI 之前，先拦截掉无效或违规请求
    """
    if not user_input or len(user_input) < 2:
        return "REFUSE"

    # 敏感词或无关词过滤
    blacklist = ['游戏', '追星', '八卦','天气']
    for word in blacklist:
        if word in user_input:
            return "REFUSE"

    return "PROCEED"