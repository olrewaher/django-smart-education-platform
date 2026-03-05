from locust import HttpUser, task, between

class StudentBehavior(HttpUser):
    # 模拟真实用户的行为：点完一个网页后，随机发阅读 2 到 5 秒
    wait_time = between(2, 5)

    def on_start(self):
        """
        前置：每个虚拟用户一上线，先模拟登录。
        请先在系统里注册一个账号：用户名 test_user，密码 123456
        """
        # 注意：这里的 "/login/" 填真实的登录路由地址
        self.client.post("/login/", data={
            "username": "test_user",
            "password": "123456"
        })

    @task(4)
    def view_index(self):
        """权重为 4：模拟学生高频访问首页和课程列表"""
        self.client.get("/")

    @task(2)
    def view_case_detail(self):
        """权重为 2：模拟学生点击进入某一个具体课程（假设课程 ID 为 1）"""
        self.client.get("/case/1/")  # 确保数据库里有 ID=1 的课程

    @task(1)
    def load_profile(self):
        """权重为 1：模拟学生偶尔去个人中心看一眼打卡日历"""
        self.client.get("/profile/")