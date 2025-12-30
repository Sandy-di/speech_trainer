from django.http import JsonResponse
from django.utils import timezone
from .models import Exercise, DailyCheckIn, PracticeRecord
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
import json

# ==========================================
#  小程序后端接口 (API Views)
# ==========================================

@csrf_exempt
def mp_login(request):
    """
    小程序登录接口
    """
    if request.method == 'POST':
        try:
            # 兼容处理：小程序传来的可能是 JSON body
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except:
            # 或者是表单数据
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)  # 关键：这会创建 Session 并返回 Cookie
            return JsonResponse({
                'status': 'success',
                'user': {'id': user.id, 'username': user.username}
            })
        else:
            return JsonResponse({'status': 'error', 'msg': '账号密码错误'})

    return JsonResponse({'status': 'error', 'msg': '仅支持POST'})


@csrf_exempt
def dashboard_data(request):
    """
    小程序首页数据接口
    """
    # 1. 权限检查 (不再使用 ID=2 测试)
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'msg': '请先登录'})

    student = request.user

    # 2. 获取或创建今天的打卡单
    today = timezone.now().date()
    checkin, created = DailyCheckIn.objects.get_or_create(
        student=student,
        date=today
    )

    # 3. 获取所有练习，按 order 排序
    exercises = Exercise.objects.all().order_by('order')

    # 4. 获取已完成的练习记录 ID
    completed_records = PracticeRecord.objects.filter(daily_checkin=checkin)
    completed_ids = set(record.exercise.id for record in completed_records)

    # 5. 构建练习列表数据
    exercises_data = []
    for ex in exercises:
        is_done = ex.id in completed_ids
        exercises_data.append({
            'id': ex.id,
            'title': ex.title,
            'isDone': is_done
        })

    # 6. 计算进度
    total_count = exercises.count()
    completed_count = len(completed_ids)
    all_done = (completed_count >= total_count) and (total_count > 0)

    # 7. 返回 JSON 数据包
    data = {
        'status': 'success',
        'studentName': student.username,
        'todayDate': today.strftime("%Y.%m.%d"),
        'totalCount': total_count,
        'completedCount': completed_count,
        'allDone': all_done,
        'isSubmitted': checkin.is_submitted,
        'exercises': exercises_data
    }

    return JsonResponse(data)


@csrf_exempt
def exercise_detail(request, exercise_id):
    """
    小程序：获取单个练习的详情
    """
    # 1. 权限检查
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'msg': '请先登录'})

    student = request.user

    try:
        # 2. 获取练习对象
        exercise = Exercise.objects.get(id=exercise_id)

        # 3. 获取今天的打卡单
        today = timezone.now().date()
        checkin, _ = DailyCheckIn.objects.get_or_create(student=student, date=today)

        # 4. 获取该练习的记录
        record = PracticeRecord.objects.filter(daily_checkin=checkin, exercise=exercise).first()

        # 5. 准备返回的数据
        data = {
            'status': 'success',
            'id': exercise.id,
            'title': exercise.title,
            'content': exercise.content,
            'demo_audio': exercise.demo_audio.url if exercise.demo_audio else '',
            'student_audio': record.student_audio.url if (record and record.student_audio) else '',
            'is_finished': True if (record and record.student_audio) else False,
            'teacher_text': record.teacher_comment_text if record else '',
            'teacher_audio': record.teacher_comment_audio.url if (record and record.teacher_comment_audio) else ''
        }
        return JsonResponse(data)

    except Exercise.DoesNotExist:
        return JsonResponse({'status': 'error', 'msg': '练习不存在'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)})


@csrf_exempt
def upload_recording(request, exercise_id):
    """
    小程序：接收录音文件上传
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '仅支持POST请求'})

    # 1. 权限检查
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'msg': '请先登录'})

    student = request.user

    try:
        # 2. 获取文件
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'status': 'error', 'msg': '未上传文件'})

        # 3. 获取相关对象
        exercise = Exercise.objects.get(id=exercise_id)
        today = timezone.now().date()
        checkin, _ = DailyCheckIn.objects.get_or_create(student=student, date=today)

        # 4. 保存或更新练习记录
        record, created = PracticeRecord.objects.get_or_create(
            daily_checkin=checkin,
            exercise=exercise,
            defaults={'student': student}
        )

        # 更新录音文件
        record.student_audio = audio_file
        record.submitted_at = timezone.now()
        record.save()

        return JsonResponse({'status': 'success', 'url': record.student_audio.url})

    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)})


@csrf_exempt
def submit_daily(request):
    """
    小程序：提交今日打卡（通知老师）
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '仅支持POST请求'})

    # 1. 权限检查
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'msg': '请先登录'})

    student = request.user

    try:
        today = timezone.now().date()
        checkin = DailyCheckIn.objects.filter(student=student, date=today).first()

        if not checkin:
            return JsonResponse({'status': 'error', 'msg': '今日尚未开始练习'})

        checkin.is_submitted = True
        checkin.save()

        return JsonResponse({'status': 'success', 'msg': '提交成功'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)})