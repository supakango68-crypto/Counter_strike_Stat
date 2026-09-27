from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

INPUT_CLASS = "w-full rounded-lg border border-white/20 bg-white/10 px-4 py-2 text-white placeholder-white/40 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400"


class StyledFormMixin:
    def _style(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class RegisterForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label="อีเมล")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้แล้ว")
        return email


class PlayerSearchForm(StyledFormMixin, forms.Form):
    query = forms.CharField(max_length=200, label="Steam ID / ลิงก์ Steam / ชื่อ Vanity")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields["query"].widget.attrs["placeholder"] = "76561197969209908"


class MatchSearchForm(PlayerSearchForm):
    limit = forms.IntegerField(min_value=1, max_value=30, initial=5, label="จำนวนแมตช์")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class CompareForm(StyledFormMixin, forms.Form):
    player1 = forms.CharField(max_length=200, label="ผู้เล่นคนที่ 1")
    player2 = forms.CharField(max_length=200, label="ผู้เล่นคนที่ 2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class NoteForm(StyledFormMixin, forms.Form):
    note = forms.CharField(max_length=200, required=False, label="บันทึกส่วนตัว")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
