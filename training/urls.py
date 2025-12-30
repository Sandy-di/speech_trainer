from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# 如果您有 api_views.py 并且需要用，请取消下面这行的注释
# from . import api_views

urlpatterns = [
    # ==========================================
    # 1. 网页端路径 (Web Pages)
    # ==========================================

    # 学员首页（打卡面板）
    path('', views.student_dashboard, name='student_dashboard'),

    # 登录/注册/退出
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('password_change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change_form.html',
             success_url='/password_change/done/'  # 修改成功后跳转的地址
         ), 
         name='password_change'),

    # 修改密码成功页面
    path('password_change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html'
         ), 
         name='password_change_done'),

    # 网页版练习详情
    path('exercise/<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),

    # 网页版老师功能
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    # 兼容旧链接（可选）
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard_alias'),

    # 老师总评页面 (Web Page)
    path('teacher/summary/<int:checkin_id>/', views.teacher_summary_view, name='teacher_summary'),

    # 单条录音点评页面 (保留)
    path('review/<int:record_id>/', views.review_submission, name='review_submission'),

    # 每日打卡综合日报 (包含点赞、总评)
    path('daily_report/<int:checkin_id>/', views.daily_report_view, name='daily_report_view'),

    # 旧版分享页
    path('share/<int:record_id>/', views.shared_record_detail, name='shared_record_detail'),
    path('share/daily/', views.daily_share_poster, name='daily_share_poster'),

    # 下载录音文件
    path('download/<int:record_id>/', views.download_record_audio, name='download_record_audio'),

    # 学员历史录音
    path('history/', views.student_history, name='student_history'),
    
    # 老师查看学员历史录音
    path('teacher/student/<int:student_id>/history/', views.teacher_student_history, name='teacher_student_history'),

    # ==========================================
    # 公告系统
    # ==========================================
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('announcement/<int:announcement_id>/stats/', views.announcement_stats, name='announcement_stats'),


    # ==========================================
    # 2. API 接口 (供网页 JS 和 小程序使用)
    # ==========================================

    # 基础接口
    path('api/test/', views.api_test, name='api_test'),
    path('api/login/', views.api_login, name='api_login'),

    # 练习数据
    path('api/exercises/', views.api_exercise_list, name='api_exercise_list'),
    path('api/exercise/<int:exercise_id>/', views.api_exercise_detail, name='api_exercise_detail'),

    # 🔥 核心业务接口 🔥
    # 1. 上传录音
    path('api/upload_practice/', views.api_upload_practice, name='api_upload_practice'),

    # 2. 🔥👇 新增：标记完成 (放弃录音但记录进度) 👇🔥
    path('api/mark_complete/', views.api_mark_practice_complete, name='api_mark_practice_complete'),

    # 3. 提交日报
    path('api/submit_daily/', views.submit_daily_checkin, name='submit_daily_checkin'),

    path('api/my_practices/', views.api_my_practice_list, name='api_my_practice_list'),

    # 老师端 API (提交总评、获取列表)
    path('api/teacher/checkins/', views.api_teacher_checkins, name='api_teacher_checkins'),
    path('api/teacher/review/', views.api_submit_review, name='api_submit_review'),
    path('api/teacher/summary/<int:checkin_id>/', views.submit_teacher_summary, name='submit_teacher_summary_api'),

    # 辅助接口 (音频列表、点赞)
    path('api/report_audios/<int:report_id>/', views.get_report_audio_urls, name='get_report_audios'),
    path('api/like/<int:checkin_id>/', views.toggle_like, name='toggle_like'),

    # ==========================================
    # 3. 小程序专用接口 (如果您还有 api_views.py)
    # ==========================================
    # 如果您确认现在的 views.py 已经够用，下面这些可以注释掉，或者确保导入了 api_views
    # path('api/mp/dashboard/', api_views.dashboard_data, name='mp_dashboard'),
    # path('api/mp/exercise/<int:exercise_id>/', api_views.exercise_detail, name='mp_exercise_detail'),
    # path('api/mp/upload/<int:exercise_id>/', api_views.upload_recording, name='mp_upload'),
    # path('api/mp/login/', api_views.mp_login, name='mp_login'),
]
