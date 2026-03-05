from django.test import TestCase
from django.contrib.auth.models import User
from common.models import CaseStudy, Category, Note


class NoteTestCase(TestCase):
    def setUp(self):
        # 预置条件：严格按照外键依赖关系构建前置数据
        self.user = User.objects.create_user(username='note_maker', password='123')
        self.category = Category.objects.create(name='计算机基础')
        self.case = CaseStudy.objects.create(title='Python 编程', category=self.category)

    def test_create_note(self):
        """测试用例 3：测试笔记的创建与外键级联关系"""
        # 模拟学生提交了一条笔记 (chapter 是 null=True，所以可以不传)
        note = Note.objects.create(
            user=self.user,
            case=self.case,
            content="Markdown 导出功能真的很实用！"
        )

        # 断言：笔记数量为 1
        self.assertEqual(Note.objects.count(), 1)
        # 断言：验证跨表查询，笔记所属的课程分类是否为“计算机基础”
        self.assertEqual(note.case.category.name, '计算机基础')
        print("✅ 测试通过：笔记创建与多表外键关联逻辑正常。")