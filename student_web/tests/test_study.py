from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from common.models import DailyStudyActivity


class StudyActivityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='diligent_student', password='123')

    def test_daily_duration_accumulation(self):
        """测试用例 5：测试每日学习总时长的累加机制"""
        today = timezone.localdate()

        # 模拟心跳包第一次发来 10 秒
        daily_record, _ = DailyStudyActivity.objects.get_or_create(user=self.user, date=today)
        daily_record.duration += 10
        daily_record.save()

        # 模拟心跳包第二次发来 20 秒
        daily_record2, _ = DailyStudyActivity.objects.get_or_create(user=self.user, date=today)
        daily_record2.duration += 20
        daily_record2.save()

        # 从数据库重新查询该记录
        final_record = DailyStudyActivity.objects.get(user=self.user, date=today)

        # 断言：今日总时长必须完美累加为 30 秒
        self.assertEqual(final_record.duration, 30)
        print("✅ 测试通过：每日学习活跃度跨请求累加算法正常。")