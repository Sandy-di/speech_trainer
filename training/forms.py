from django.contrib.auth.forms import UserCreationForm
from django import forms


class ChineseUserCreationForm(UserCreationForm):
    """自定义用户注册表单，字段标签为中文"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置字段标签为中文
        self.fields['username'].label = '用户名'
        self.fields['password1'].label = '密码'
        self.fields['password2'].label = '确认密码'
        
        # 设置帮助文本为中文
        self.fields['username'].help_text = '请使用中文真实姓名注册，不可添加其他非中文字符，对给您带来的不便表示歉意。'
        self.fields['password1'].help_text = '您的密码必须包含至少8个字符，不能是纯数字，不能与您的个人信息太相似。'
        self.fields['password2'].help_text = '请再次输入密码以确认。'
        
        self.fields['password1'].widget.attrs['placeholder'] = '请输入密码'
        self.fields['password2'].widget.attrs['placeholder'] = '请再次输入密码'

from .models import Announcement

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'audio_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入公告标题', 'style': 'width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #ddd;'}),
        }

