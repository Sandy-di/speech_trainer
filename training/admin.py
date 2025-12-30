from django.contrib import admin
from .models import Exercise, PracticeRecord, DailyCheckIn, Announcement, ReadRecord

# 1. 练习管理
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')

# 2. 录音内联显示 (嵌在打卡本里)
class PracticeRecordInline(admin.TabularInline):
    model = PracticeRecord
    readonly_fields = ('exercise', 'student', 'student_audio', 'submitted_at')
    fields = ('exercise', 'student_audio', 'teacher_comment_text', 'teacher_comment_audio')
    extra = 0
    can_delete = False

# 3. 每日打卡管理 (老师批改主界面)
@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'is_submitted', 'created_at')
    list_filter = ('is_submitted', 'date', 'student')
    inlines = [PracticeRecordInline] # 把录音嵌进去
    ordering = ('-date',)

# 4. 公告管理
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    ordering = ('-created_at',)

@admin.register(ReadRecord)
class ReadRecordAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'student', 'read_at')
    list_filter = ('announcement', 'student')
