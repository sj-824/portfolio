from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views import generic
from .forms import (
    LoginForm, UserCreateForm
)

User = get_user_model()

# Create your views here.
class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'accounts/login.html'

class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'accounts/homepage.html'
    # model = ProfileModel

class UserCreate(generic.CreateView):
    form_class = UserCreateForm
    template_name = 'accounts/user_create.html'

    def form_valid(self,form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject = render_to_string('accounts/mail_template/create/subject.txt', context)
        message = render_to_string('accounts/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('accounts:user_create_done')

class UserCreateDone(generic.TemplateView):
    template_name = 'accounts/user_create_done.html'

class UserCreateComplete(generic.TemplateView):
    template_name = 'accounts/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録とする
                    user.is_active = True
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()

class UserDelete(LoginRequiredMixin, generic.View):
    def get(self, *args, **kwargs):
        user = User.objects.get(username = self.request.user.username)
        user.is_active = False
        user.save()
        logout(self.request)
        return render(self.request,'accounts/user_delete.html')

class HomePage(generic.TemplateView):
    template_name = 'accounts/homepage.html'

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:logout')
        
        return super().get(request, **kwargs)