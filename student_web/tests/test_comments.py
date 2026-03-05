from django.test import TestCase
from django.contrib.auth.models import User
from common.models import CaseStudy, Category, Comment


class CommentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='123')
        self.category = Category.objects.create(name='软件工程')
        self.case = CaseStudy.objects.create(title='系统测试方法', category=self.category)

    def test_post_comment(self):
        """测试用例 4：测试互动评论区的发布逻辑"""
        comment = Comment.objects.create(
            user=self.user,
            case=self.case,
            content="老师讲得非常透彻，满分！"
        )

        # 断言：评论成功落库，且内容一致
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.content, "老师讲得非常透彻，满分！")
        print("✅ 测试通过：评论区互动发布逻辑正常。")