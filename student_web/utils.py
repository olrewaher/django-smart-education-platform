import os
import time
from django.conf import settings

# 尝试导入 flashtext，如果没安装则自动降级容灾，防止报错
try:
    from flashtext import KeywordProcessor
except ImportError:
    KeywordProcessor = None


class SensitiveFilter:
    """
    敏感词过滤器
    集成双引擎：支持 'DFA' (FlashText算法) 和 'SIMPLE' (原生Set算法)
    特点：单例模式、懒加载、多词库自动合并、自动降级
    """
    _instance = None

    # 🔥 引擎开关
    ENGINE_TYPE = 'DFA'

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SensitiveFilter, cls).__new__(cls)
            cls._instance._init_resources()
        return cls._instance

    def _init_resources(self):
        """初始化资源"""
        self._keywords_set = set()
        self._keyword_processor = None

        if self.ENGINE_TYPE == 'DFA':
            if KeywordProcessor:
                self._keyword_processor = KeywordProcessor()
            else:
                print("⚠️ [系统告警] 未检测到 flashtext 库，已自动降级为 SIMPLE 模式。")
                self.ENGINE_TYPE = 'SIMPLE'

        self._load_all_dictionaries()

    def _load_all_dictionaries(self):
        """核心逻辑：扫描 sensitive_dicts 目录下所有 .txt 文件并合并加载"""

        # 敏感词库文件夹名字改为 sensitive_dicts
        data_dir = os.path.join(settings.BASE_DIR, 'sensitive_dicts')

        # 如果目录不存在，自动创建一个
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                print(f"ℹ️ [初始化] 自动创建敏感词目录: {data_dir}")
                # 创建示例文件
                with open(os.path.join(data_dir, 'sample.txt'), 'w', encoding='utf-8') as f:
                    f.write("笨蛋\n坏人\n")
            except Exception as e:
                print(f"❌ [错误] 创建目录失败: {e}")
                return

        print(f"🚀 [敏感词引擎] 正在启动... 当前模式: {self.ENGINE_TYPE}")

        total_words = 0
        start_time = time.time()
        file_count = 0

        # 遍历目录下所有 txt 文件
        for root, dirs, files in os.walk(data_dir):
            for filename in files:
                if filename.endswith('.txt'):
                    file_path = os.path.join(root, filename)
                    file_count += 1
                    try:
                        current_count = 0
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                word = line.strip()
                                if word:
                                    if self.ENGINE_TYPE == 'DFA':
                                        self._keyword_processor.add_keyword(word)
                                    else:
                                        self._keywords_set.add(word)
                                    current_count += 1
                        total_words += current_count
                    except Exception as e:
                        print(f"   ❌ 加载失败 {filename}: {e}")

        cost = (time.time() - start_time) * 1000
        print(f"✅ [敏感词引擎] 加载完毕。耗时: {cost:.2f}ms")
        print(f"   - 词库目录: {data_dir}")
        print(f"   - 词库文件数: {file_count}")
        print(f"   - 敏感词总数: {total_words}")
        print("--------------------------------------------------")

    def check(self, content):
        if not content:
            return False, None

        if self.ENGINE_TYPE == 'DFA':
            found_list = self._keyword_processor.extract_keywords(content)
            if found_list:
                return True, found_list[0]
            return False, None
        else:
            for word in self._keywords_set:
                if word in content:
                    return True, word
            return False, None

    def reload(self):
        self._init_resources()


# 全局单例对象
filter_service = SensitiveFilter()