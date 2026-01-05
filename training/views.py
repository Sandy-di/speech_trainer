from django.utils import timezone  # 核心引入
import datetime
import json
import os

from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from .forms import ChineseUserCreationForm, AnnouncementForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Max, Q

# 引入我们定义的数据模型
from .models import (
    Exercise, PracticeRecord, DailyCheckIn, Announcement, ReadRecord,
    StudentProfile, Achievement, StudentAchievement, BuddyPair, Encouragement
)

# ==========================================
# 工具函数
# ==========================================
def get_week_start():
    today = timezone.localdate()
    start = today - datetime.timedelta(days=today.weekday())
    return start

def get_or_create_profile(user):
    """获取或创建学员游戏档案"""
    profile, created = StudentProfile.objects.get_or_create(user=user)
    return profile

def add_experience(user, exp_amount, reason="练习"):
    """为用户增加经验值并检查成就"""
    profile = get_or_create_profile(user)
    profile.experience_points += exp_amount
    profile.update_level()
    profile.save()
    
    # 检查经验值相关成就
    check_achievements(user, profile)
    return profile

def update_practice_streak(user):
    """更新连续练习天数"""
    profile = get_or_create_profile(user)
    today = timezone.localdate()
    
    if profile.last_practice_date is None:
        # 首次练习
        profile.streak_days = 1
        profile.total_practice_days = 1
    elif profile.last_practice_date == today:
        # 今天已经练习过，不重复计算
        pass
    elif profile.last_practice_date == today - datetime.timedelta(days=1):
        # 连续练习
        profile.streak_days += 1
        profile.total_practice_days += 1
    else:
        # 断了，重新开始
        profile.streak_days = 1
        profile.total_practice_days += 1
    
    profile.last_practice_date = today
    profile.save()
    
    # 计算连续天数奖励经验 (最高50)
    streak_bonus = min(profile.streak_days * 5, 50)
    
    # 检查连续天数相关成就
    check_achievements(user, profile)
    
    return profile, streak_bonus

def check_achievements(user, profile):
    """检查并解锁成就"""
    unlocked = []
    all_achievements = Achievement.objects.all()
    
    for achievement in all_achievements:
        # 检查是否已获得
        if StudentAchievement.objects.filter(student=user, achievement=achievement).exists():
            continue
        
        # 根据条件类型检查
        earned = False
        if achievement.condition_type == 'streak' and profile.streak_days >= achievement.condition_value:
            earned = True
        elif achievement.condition_type == 'total_days' and profile.total_practice_days >= achievement.condition_value:
            earned = True
        elif achievement.condition_type == 'exp' and profile.experience_points >= achievement.condition_value:
            earned = True
        elif achievement.condition_type == 'recordings' and profile.total_recordings >= achievement.condition_value:
            earned = True
        elif achievement.condition_type == 'level' and profile.level >= achievement.condition_value:
            earned = True
        elif achievement.condition_type == 'first' and profile.total_recordings >= 1:
            earned = True
        
        if earned:
            StudentAchievement.objects.create(student=user, achievement=achievement)
            # 成就奖励经验
            profile.experience_points += achievement.exp_reward
            profile.save()
            unlocked.append(achievement)
    
    return unlocked

def get_buddy_info(user):
    """获取伙伴信息"""
    pair = BuddyPair.objects.filter(
        Q(student_a=user) | Q(student_b=user),
        is_active=True
    ).first()
    
    if not pair:
        return None
    
    buddy = pair.get_buddy(user)
    if not buddy:
        return None
    
    # 获取伙伴今日练习进度
    today = timezone.localdate()
    buddy_records_today = PracticeRecord.objects.filter(
        student=buddy,
        submitted_at__date=today
    ).count()
    
    total_exercises = Exercise.objects.count()
    
    # 获取伙伴的游戏档案
    buddy_profile = get_or_create_profile(buddy)
    
    # 获取未读鼓励消息数
    unread_count = Encouragement.objects.filter(
        pair=pair,
        sender=buddy,
        is_read=False
    ).count()
    
    return {
        'buddy': buddy,
        'pair': pair,
        'profile': buddy_profile,
        'today_progress': buddy_records_today,
        'total_exercises': total_exercises,
        'unread_encouragements': unread_count,
    }

# ==========================================
# 第一部分：电脑网页版视图
# ==========================================

@login_required
def student_dashboard(request):
    today = timezone.localdate()
    start_of_week = get_week_start()

    checkin, created = DailyCheckIn.objects.get_or_create(student=request.user, date=today)
    
    # 分开查询普通练习和进阶练习
    normal_exercises = Exercise.objects.filter(is_advanced=False).order_by('order')
    advanced_exercises = Exercise.objects.filter(is_advanced=True).order_by('order')
    
    # 打卡只计算普通练习
    total_exercises = normal_exercises.count()

    daily_records = PracticeRecord.objects.filter(
        student=request.user,
        submitted_at__date=today
    )
    completed_ids = set(daily_records.values_list('exercise_id', flat=True))
    
    # 普通练习完成数
    normal_completed_count = sum(1 for e in normal_exercises if e.id in completed_ids)
    # 进阶练习完成数
    advanced_completed_count = sum(1 for e in advanced_exercises if e.id in completed_ids)

    all_done = normal_completed_count >= total_exercises and total_exercises > 0

    is_submitted_to_teacher = DailyCheckIn.objects.filter(
        student=request.user,
        date__gte=start_of_week,
        is_submitted=True
    ).exists()

    total_today_checkins = PracticeRecord.objects.filter(
        submitted_at__date=today
    ).values('student').distinct().count()

    latest_records = PracticeRecord.objects.filter(
        submitted_at__date=today
    ).select_related('student', 'exercise').order_by('-submitted_at')[:8]

    # 游戏化信息
    profile = get_or_create_profile(request.user)
    achievements_count = StudentAchievement.objects.filter(student=request.user).count()
    
    # 伙伴信息
    buddy_info = get_buddy_info(request.user)

    context = {
        'normal_exercises': normal_exercises,
        'advanced_exercises': advanced_exercises,
        'completed_ids': completed_ids,
        'completed_count': normal_completed_count,
        'total_count': total_exercises,
        'advanced_completed_count': advanced_completed_count,
        'advanced_total_count': advanced_exercises.count(),
        'all_done': all_done,
        'is_submitted_to_teacher': is_submitted_to_teacher,
        'checkin_id': checkin.id,
        'total_today_checkins': total_today_checkins,
        'latest_records': latest_records,
        'latest_announcement': Announcement.objects.first(),
        # 游戏化数据
        'profile': profile,
        'achievements_count': achievements_count,
        'exp_progress': profile.exp_progress(),
        'exp_for_next': profile.exp_for_next_level(),
        # 伙伴数据
        'buddy_info': buddy_info,
    }
    return render(request, 'training/dashboard.html', context)

@login_required
def exercise_detail(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    start_of_week = get_week_start()

    record = PracticeRecord.objects.filter(
        student=request.user,
        exercise=exercise,
        submitted_at__date__gte=start_of_week
    ).order_by('-submitted_at').first()

    return render(request, 'training/exercise_detail.html', {'exercise': exercise, 'record': record})

@login_required
def teacher_dashboard(request):
    if not request.user.is_staff: return redirect('student_dashboard')
    start_of_week = get_week_start()
    today = timezone.localdate()
    
    # 获取所有学员
    all_students = User.objects.filter(is_staff=False).order_by('username')
    
    # 获取本周已提交的打卡
    recent_checkins = DailyCheckIn.objects.filter(
        date__gte=start_of_week,
        is_submitted=True
    ).values('student').annotate(latest_date=Max('date'))

    checkins = []
    for item in recent_checkins:
        ci = DailyCheckIn.objects.filter(student__id=item['student'], date=item['latest_date']).first()
        if ci: checkins.append(ci)
    checkins.sort(key=lambda x: x.date, reverse=True)
    
    # 统计每个学员的打卡和作业情况
    student_stats = []
    for student in all_students:
        # 本周打卡次数
        week_checkins = DailyCheckIn.objects.filter(
            student=student,
            date__gte=start_of_week,
            is_submitted=True
        ).count()
        
        # 本周练习记录数（有录音的）
        week_records = PracticeRecord.objects.filter(
            student=student,
            submitted_at__date__gte=start_of_week,
            student_audio__isnull=False
        ).count()
        
        # 总历史录音数
        total_records = PracticeRecord.objects.filter(
            student=student,
            student_audio__isnull=False
        ).count()
        
        # 今日是否打卡
        today_checkin = DailyCheckIn.objects.filter(
            student=student,
            date=today,
            is_submitted=True
        ).exists()
        
        # 今日练习数
        today_records = PracticeRecord.objects.filter(
            student=student,
            submitted_at__date=today,
            student_audio__isnull=False
        ).count()
        
        student_stats.append({
            'student': student,
            'week_checkins': week_checkins,
            'week_records': week_records,
            'total_records': total_records,
            'today_checkin': today_checkin,
            'today_records': today_records,
        })
    
    # 按本周打卡次数排序
    student_stats.sort(key=lambda x: (x['week_checkins'], x['week_records']), reverse=True)
    
    return render(request, 'training/teacher_dashboard.html', {
        'checkins': checkins,
        'student_stats': student_stats,
        'start_of_week': start_of_week,
        'today': today,
        'announcements': Announcement.objects.all().order_by('-created_at')[:10],
    })

@login_required
def teacher_summary_view(request, checkin_id):
    checkin = get_object_or_404(DailyCheckIn, id=checkin_id)
    if not request.user.is_staff: return redirect('student_dashboard')
    if request.method == 'POST':
        checkin.teacher_summary = request.POST.get('summary_text')
        if request.FILES.get('summary_audio'): checkin.teacher_audio = request.FILES.get('summary_audio')
        checkin.save()
        return redirect('teacher_dashboard')
    return render(request, 'training/teacher_summary.html', {'checkin': checkin})

@login_required
def review_submission(request, record_id):
    if not request.user.is_staff: return redirect('student_dashboard')
    record = get_object_or_404(PracticeRecord, id=record_id)
    if request.method == "POST":
        if request.POST.get('comment_text'): record.teacher_comment_text = request.POST.get('comment_text')
        if request.FILES.get('audio_data'): record.teacher_comment_audio = request.FILES.get('audio_data')
        record.save(); return JsonResponse({'status': 'success'})
    return render(request, 'training/review_detail.html', {'record': record})

def register(request):
    if request.method == 'POST':
        form = ChineseUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user); return redirect('student_dashboard')
    else: form = ChineseUserCreationForm()
    return render(request, 'training/register.html', {'form': form})

def custom_login(request):
    """自定义登录视图，用于显示错误信息"""
    if request.user.is_authenticated:
        return redirect('student_dashboard')
    
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('student_dashboard')
        else:
            error_message = '用户名或密码错误，请重试'
    
    return render(request, 'training/login.html', {'error_message': error_message})

def custom_logout(request): logout(request); return redirect('login')

def shared_record_detail(request, record_id):
    record = get_object_or_404(PracticeRecord, id=record_id)
    if request.method == "POST":
        if not request.user.is_staff: return JsonResponse({'status': 'error', 'msg': '无权操作'})
        if request.POST.get('comment_text'): record.teacher_comment_text = request.POST.get('comment_text')
        if request.FILES.get('audio_data'): record.teacher_comment_audio = request.FILES.get('audio_data')
        record.save(); return JsonResponse({'status': 'success'})
    return render(request, 'training/shared_record.html', {'record': record, 'exercise': record.exercise})

@login_required
def download_record_audio(request, record_id):
    try: record = PracticeRecord.objects.get(id=record_id)
    except: raise Http404
    if record.student != request.user and not request.user.is_staff: return HttpResponse(status=403)
    if record.student_audio and os.path.exists(record.student_audio.path):
        with open(record.student_audio.path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="audio/mpeg")
            response['Content-Disposition'] = f'attachment; filename="rec_{record.id}.webm"'
            return response
    raise Http404

# 🔥🔥🔥 修改后的核心函数：只展示本周每个练习的最新提交 🔥🔥🔥
def daily_report_view(request, checkin_id):
    checkin = get_object_or_404(DailyCheckIn, id=checkin_id)

    # 1. 计算本周起始时间 (基于打卡日期所在的周一)
    start_of_week = checkin.date - datetime.timedelta(days=checkin.date.weekday())

    # 2. 获取本周该学生的所有练习记录（按提交时间正序排列：旧 -> 新）
    # 使用 select_related 优化查询
    week_records = PracticeRecord.objects.filter(
        student=checkin.student,
        submitted_at__date__gte=start_of_week
    ).select_related('exercise').order_by('submitted_at')

    # 3. 【核心逻辑】使用字典去重，只保留每个练习的最后一条（最新）记录
    # 原理：字典的 key 是唯一的，后遍历到的记录会覆盖先遍历到的
    latest_record_map = {}
    for record in week_records:
        latest_record_map[record.exercise.id] = record

    # 4. 将去重后的记录转回列表，并按练习的顺序 (exercise.order) 排序用于展示
    # 注意：这里假设 Exercise 模型有 order 字段
    records = sorted(latest_record_map.values(), key=lambda r: r.exercise.order)

    is_liked = request.user.is_authenticated and checkin.likes.filter(id=request.user.id).exists()

    context = {
        'checkin': checkin,
        'records': records,
        'is_liked': is_liked,
        'total_likes': checkin.total_likes(),
        'is_teacher': request.user.is_staff if request.user.is_authenticated else False,
        'is_me': request.user == checkin.student,
        'total_today_checkins': DailyCheckIn.objects.filter(date=checkin.date).count(),
    }
    return render(request, 'training/daily_report.html', context)

@csrf_exempt
@login_required
def submit_teacher_summary(request, checkin_id):
    if not request.user.is_staff: return JsonResponse({"status": "error"})
    if request.method == 'POST':
        checkin = get_object_or_404(DailyCheckIn, id=checkin_id)
        if request.POST.get('summary_text'): checkin.teacher_summary = request.POST.get('summary_text')
        if request.FILES.get('summary_audio'): checkin.teacher_audio = request.FILES.get('summary_audio')
        checkin.save(); return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})

@csrf_exempt
@login_required
def toggle_like(request, checkin_id):
    checkin = get_object_or_404(DailyCheckIn, id=checkin_id)
    if checkin.likes.filter(id=request.user.id).exists(): checkin.likes.remove(request.user); liked=False
    else: checkin.likes.add(request.user); liked=True
    return JsonResponse({"status": "success", "liked": liked, "count": checkin.total_likes()})

@login_required
def daily_share_poster(request):
    today = timezone.localdate()
    records = PracticeRecord.objects.filter(student=request.user, submitted_at__date=today)
    return render(request, 'training/daily_share.html', {'today_count': records.count(), 'username': request.user.username, 'date': today})

@login_required
def student_history(request):
    """学员查看历史录音"""
    # 获取所有有录音的练习记录，按时间倒序
    records = PracticeRecord.objects.filter(
        student=request.user,
        student_audio__isnull=False
    ).select_related('exercise').order_by('-submitted_at')
    
    # 按日期分组
    records_by_date = {}
    for record in records:
        date_key = record.submitted_at.date()
        if date_key not in records_by_date:
            records_by_date[date_key] = []
        records_by_date[date_key].append(record)
    
    # 转换为列表并按日期倒序
    history_list = sorted(records_by_date.items(), key=lambda x: x[0], reverse=True)
    
    return render(request, 'training/student_history.html', {
        'history_list': history_list,
        'total_records': records.count()
    })

@login_required
def teacher_student_history(request, student_id):
    """老师查看指定学员的历史录音"""
    if not request.user.is_staff: return redirect('student_dashboard')
    
    student = get_object_or_404(User, id=student_id, is_staff=False)
    
    # 获取所有有录音的练习记录，按时间倒序
    records = PracticeRecord.objects.filter(
        student=student,
        student_audio__isnull=False
    ).select_related('exercise').order_by('-submitted_at')
    
    # 按日期分组
    records_by_date = {}
    for record in records:
        date_key = record.submitted_at.date()
        if date_key not in records_by_date:
            records_by_date[date_key] = []
        records_by_date[date_key].append(record)
    
    # 转换为列表并按日期倒序
    history_list = sorted(records_by_date.items(), key=lambda x: x[0], reverse=True)
    
    return render(request, 'training/teacher_student_history.html', {
        'student': student,
        'history_list': history_list,
        'total_records': records.count()
    })


# ==========================================
# API 接口 (Core API)
# ==========================================

def api_test(request): return JsonResponse({'status': 'success'})

# 删除历史录音记录
@csrf_exempt
@login_required
def api_delete_practice_record(request, record_id):
    """删除历史录音记录"""
    if request.method == 'POST':
        try:
            record = PracticeRecord.objects.get(id=record_id, student=request.user)
            # 删除关联的音频文件
            if record.student_audio:
                record.student_audio.delete(save=False)
            record.delete()
            return JsonResponse({'status': 'success', 'msg': '录音已删除'})
        except PracticeRecord.DoesNotExist:
            return JsonResponse({'status': 'error', 'msg': '记录不存在'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'error', 'msg': 'POST only'})

@csrf_exempt
def api_upload_practice(request):
    if request.method == 'POST':
        try:
            audio_file = request.FILES.get('audio_file')
            exercise_id = request.POST.get('exercise_id')
            user = request.user if request.user.is_authenticated else None

            if not user and request.POST.get('user_id'):
                 try: user = User.objects.get(id=request.POST.get('user_id'))
                 except: return JsonResponse({'status': 'error', 'msg': '用户不存在'})
            if not user: return JsonResponse({'status': 'error', 'msg': '未登录'})
            if not audio_file or not exercise_id: return JsonResponse({'status': 'error', 'msg': '参数缺失'})

            exercise = Exercise.objects.get(id=exercise_id)
            today = timezone.localdate()
            start_of_week = get_week_start()

            daily_checkin_today, _ = DailyCheckIn.objects.get_or_create(
                student=user, date=today, defaults={'is_submitted': False}
            )

            existing_record = PracticeRecord.objects.filter(
                student=user,
                exercise=exercise,
                submitted_at__date__gte=start_of_week
            ).first()

            is_new_recording = existing_record is None

            if existing_record:
                existing_record.student_audio = audio_file
                existing_record.submitted_at = timezone.now()
                existing_record.daily_checkin = daily_checkin_today
                existing_record.save()
                msg = '本周最佳作业已更新！'
            else:
                PracticeRecord.objects.create(
                    student=user,
                    exercise=exercise,
                    student_audio=audio_file,
                    daily_checkin=daily_checkin_today
                )
                msg = '上传成功，设为本周最佳！'

            # ==========================================
            # 游戏化逻辑
            # ==========================================
            profile = get_or_create_profile(user)
            exp_earned = 0
            
            # 1. 基础经验：每次录音 +10 XP
            exp_earned += 10
            
            # 2. 更新连续练习天数并获取奖励
            profile, streak_bonus = update_practice_streak(user)
            exp_earned += streak_bonus
            
            # 3. 新录音增加录音计数
            if is_new_recording:
                profile.total_recordings += 1
                profile.save()
            
            # 4. 检查是否完成今日所有练习（额外奖励）
            total_exercises = Exercise.objects.count()
            today_records = PracticeRecord.objects.filter(
                student=user,
                submitted_at__date=today
            ).values('exercise_id').distinct().count()
            
            if today_records >= total_exercises:
                exp_earned += 30  # 完成所有练习额外奖励
            
            # 5. 添加经验值
            add_experience(user, exp_earned)
            
            # 返回带经验值信息的响应
            return JsonResponse({
                'status': 'success', 
                'msg': msg,
                'exp_earned': exp_earned,
                'streak_days': profile.streak_days
            })
        except Exception as e: return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'error'})

@csrf_exempt
@login_required
def submit_daily_checkin(request):
    if request.method == 'POST':
        try:
            today = timezone.localdate()
            start_of_week = get_week_start()
            daily_checkin, _ = DailyCheckIn.objects.get_or_create(student=request.user, date=today)

            count = PracticeRecord.objects.filter(student=request.user, submitted_at__date__gte=start_of_week).count()
            if count == 0:
                return JsonResponse({"status": "error", "msg": "本周还没有上传任何练习哦"})

            daily_checkin.is_submitted = True
            daily_checkin.save()
            return JsonResponse({"status": "success", "msg": "本周作业已同步给老师！"})
        except Exception as e: return JsonResponse({"status": "error", "msg": str(e)})
    return JsonResponse({"status": "error"})

def api_exercise_list(request):
    exercises = Exercise.objects.all().order_by('order')
    data = [{'id': ex.id, 'title': ex.title, 'demo_audio': request.build_absolute_uri(ex.demo_audio.url) if ex.demo_audio else ''} for ex in exercises]
    return JsonResponse({'status': 'success', 'data': data})

def api_exercise_detail(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    return JsonResponse({'status': 'success', 'data': {'id': exercise.id, 'title': exercise.title, 'content': exercise.content, 'demo_audio': request.build_absolute_uri(exercise.demo_audio.url) if exercise.demo_audio else ''}})

@csrf_exempt
def api_login(request):
    if request.method != 'POST': return JsonResponse({'status': 'error'})
    try: data = json.loads(request.body)
    except: return JsonResponse({'status': 'error'})
    if 'username' in data:
        user = authenticate(username=data['username'], password=data['password'])
        if user: login(request, user); return JsonResponse({'status': 'success', 'msg': 'OK', 'is_staff': user.is_staff})
        return JsonResponse({'status': 'error', 'msg': 'Fail'})
    return JsonResponse({'status': 'error'})

def api_my_practice_list(request):
    user = request.user if request.user.is_authenticated else None
    if not user: return JsonResponse({'status': 'error'})
    checkins = DailyCheckIn.objects.filter(student=user).order_by('-date')
    data = [{'date': ci.date, 'is_submitted': ci.is_submitted} for ci in checkins]
    return JsonResponse({'status': 'success', 'data': data})

@login_required
def api_teacher_checkins(request):
    if not request.user.is_staff: return JsonResponse({"status": "error"})
    checkins = DailyCheckIn.objects.filter(is_submitted=True).order_by('-date')
    return JsonResponse({"checkins": []})

@login_required
def api_submit_review(request): return JsonResponse({"status": "success"})

def get_report_audio_urls(request, report_id):
    try:
        checkin = DailyCheckIn.objects.get(id=report_id)
        records = checkin.records.all()
        # 🔥 修改：增加判断，防止空音频报错
        audio_list = [{'url': r.student_audio.url, 'name': r.student_audio.name} for r in records if r.student_audio]
        return JsonResponse({'status': 'success', 'files': audio_list})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

# ==========================================
# 公告系统视图
# ==========================================

@login_required
def create_announcement(request):
    if not request.user.is_staff: return redirect('student_dashboard')
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            return redirect('teacher_dashboard')
    else:
        form = AnnouncementForm()
    return render(request, 'training/announcement_form.html', {'form': form})

@login_required
def edit_announcement(request, announcement_id):
    if not request.user.is_staff: return redirect('student_dashboard')
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            return redirect('announcement_detail', announcement_id=announcement.id)
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'training/announcement_form.html', {'form': form, 'is_edit': True, 'announcement': announcement})

@login_required
def delete_announcement(request, announcement_id):
    if not request.user.is_staff: return redirect('student_dashboard')
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.method == 'POST':
        announcement.delete()
        return redirect('teacher_dashboard')
    return redirect('teacher_dashboard')

@login_required
def announcement_detail(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if not request.user.is_staff:
        ReadRecord.objects.get_or_create(announcement=announcement, student=request.user)
    return render(request, 'training/announcement_detail.html', {'announcement': announcement})

@login_required
def announcement_stats(request, announcement_id):
    if not request.user.is_staff: return redirect('student_dashboard')
    announcement = get_object_or_404(Announcement, id=announcement_id)
    all_students = User.objects.filter(is_staff=False)
    read_records = ReadRecord.objects.filter(announcement=announcement).values_list('student_id', flat=True)
    read_list = [s for s in all_students if s.id in read_records]
    unread_list = [s for s in all_students if s.id not in read_records]
    return render(request, 'training/announcement_stats.html', {
        'announcement': announcement,
        'read_list': read_list,
        'unread_list': unread_list,
        'read_count': len(read_list),
        'total_count': all_students.count()
    })


# ==========================================
# 互帮系统 API
# ==========================================

@csrf_exempt
@login_required
def api_send_encouragement(request):
    """发送鼓励消息给伙伴"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({'status': 'error', 'msg': '消息不能为空'})
            
            if len(message) > 500:
                return JsonResponse({'status': 'error', 'msg': '消息太长，最多500字'})
            
            # 获取配对信息
            pair = BuddyPair.objects.filter(
                Q(student_a=request.user) | Q(student_b=request.user),
                is_active=True
            ).first()
            
            if not pair:
                return JsonResponse({'status': 'error', 'msg': '您还没有配对伙伴'})
            
            # 创建鼓励消息
            Encouragement.objects.create(
                pair=pair,
                sender=request.user,
                message=message
            )
            
            return JsonResponse({'status': 'success', 'msg': '鼓励消息已发送！'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'error', 'msg': 'POST only'})


@login_required
def api_get_encouragements(request):
    """获取收到的鼓励消息"""
    pair = BuddyPair.objects.filter(
        Q(student_a=request.user) | Q(student_b=request.user),
        is_active=True
    ).first()
    
    if not pair:
        return JsonResponse({'status': 'success', 'messages': []})
    
    buddy = pair.get_buddy(request.user)
    
    # 获取来自伙伴的未读消息
    messages = Encouragement.objects.filter(
        pair=pair,
        sender=buddy,
        is_read=False
    ).order_by('-created_at')[:10]
    
    messages_data = [{
        'id': m.id,
        'message': m.message,
        'time': m.created_at.strftime('%m-%d %H:%M')
    } for m in messages]
    
    return JsonResponse({
        'status': 'success',
        'messages': messages_data,
        'buddy_name': buddy.username
    })


@csrf_exempt
@login_required
def api_mark_encouragement_read(request, msg_id):
    """标记鼓励消息为已读"""
    if request.method == 'POST':
        try:
            msg = Encouragement.objects.get(id=msg_id)
            # 验证这条消息是发给当前用户的
            buddy = msg.pair.get_buddy(msg.sender)
            if buddy != request.user:
                return JsonResponse({'status': 'error', 'msg': '无权操作'})
            
            msg.is_read = True
            msg.save()
            return JsonResponse({'status': 'success'})
        except Encouragement.DoesNotExist:
            return JsonResponse({'status': 'error', 'msg': '消息不存在'})
    return JsonResponse({'status': 'error', 'msg': 'POST only'})


@login_required
def achievements_page(request):
    """成就墙页面"""
    profile = get_or_create_profile(request.user)
    
    # 获取所有成就
    all_achievements = Achievement.objects.all()
    
    # 获取用户已解锁的成就
    earned_ids = set(StudentAchievement.objects.filter(
        student=request.user
    ).values_list('achievement_id', flat=True))
    
    achievements_list = []
    for ach in all_achievements:
        achievements_list.append({
            'achievement': ach,
            'earned': ach.id in earned_ids
        })
    
    return render(request, 'training/achievements.html', {
        'profile': profile,
        'achievements_list': achievements_list,
        'earned_count': len(earned_ids),
        'total_count': all_achievements.count()
    })

