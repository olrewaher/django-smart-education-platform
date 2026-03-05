
# Create your views here.
from django.shortcuts import render, redirect
from django.conf import settings
from .forms import RegisterForm

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .utils import set_captcha_mode  # 导入同一个文件夹下的 utils


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 到了这里，说明验证码（不管是云端的还是本地的）都已经通过了
            print("验证通过，注册用户:", form.cleaned_data['username'])
            # save_user(form.cleaned_data)
            return redirect('/login/')
    else:
        form = RegisterForm()

    # 将 Site Key 传入模板上下文
    context = {
        'form': form,
        'turnstile_site_key': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
    }
    return render(request, 'register.html', context)


# 加上这个装饰器，防止普通用户乱点，只有管理员能切
@staff_member_required
def switch_captcha(request, mode):
    if mode == 'local':
        set_captcha_mode(False)
        return HttpResponse("✅ 已切换为：本地验证码 (Local)")
    elif mode == 'saas':
        set_captcha_mode(True)
        return HttpResponse("✅ 已切换为：Cloudflare (SaaS)")
    else:
        return HttpResponse("❌ 参数错误", status=400)