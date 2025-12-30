from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('training.urls')), # 把首页请求转给 training 应用
    path('ckeditor/', include('ckeditor_uploader.urls')), # <--- 新增这一行
]

# 这段代码让开发环境能访问录音文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)