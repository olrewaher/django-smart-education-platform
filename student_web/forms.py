from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from common.models import Note, Comment

# ==============================================================================
# 1. 扩展注册表单 (新增)
# ==============================================================================
class StudentRegistrationForm(UserCreationForm):
    """
    自定义学生注册表单
    继承自 Django 原生 UserCreationForm，额外增加邮箱字段
    """
    email = forms.EmailField(
        label="电子邮箱",
        required=True,  # 🔥 设为必填，这是找回密码的关键
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg bg-light border-start-0',
            'placeholder': '请输入邮箱 (用于找回密码)',
            'style': 'border-radius: 0 8px 8px 0;' # 配合 input-group 的样式
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # 🔥 指定字段顺序：用户名 -> 邮箱 -> 密码1 -> 密码2
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 统一优化所有字段的默认样式
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control form-control-lg bg-light border-start-0'
            field.widget.attrs['style'] = 'border-radius: 0 8px 8px 0;'


# ==============================================================================
# 2. 笔记表单 (保留)
# ==============================================================================
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '在此处记录您的学习心得（支持 Markdown 格式）...'
            })
        }
        error_messages = {
            'content': {'required': '笔记内容不能为空哦！'}
        }


# ==============================================================================
# 3. 评论表单 (保留)
# ==============================================================================
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '发表你的看法，与其他同学交流...'
            })
        }