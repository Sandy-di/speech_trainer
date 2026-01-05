from django.contrib import admin
from .models import (
    Exercise, PracticeRecord, DailyCheckIn, Announcement, ReadRecord,
    StudentProfile, Achievement, StudentAchievement, BuddyPair, Encouragement
)

# 1. 练习管理
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_advanced')
    list_editable = ('order', 'is_advanced')
    list_filter = ('is_advanced',)

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


# ==========================================
# 5. 游戏化系统管理
# ==========================================

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'experience_points', 'streak_days', 'total_practice_days', 'total_recordings')
    list_filter = ('level',)
    search_fields = ('user__username',)
    ordering = ('-experience_points',)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'condition_type', 'condition_value', 'exp_reward', 'order')
    list_editable = ('order', 'exp_reward')
    ordering = ('order',)

@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ('student', 'achievement', 'earned_at')
    list_filter = ('achievement',)
    search_fields = ('student__username',)


# ==========================================
# 6. 互帮系统管理
# ==========================================

@admin.register(BuddyPair)
class BuddyPairAdmin(admin.ModelAdmin):
    list_display = ('student_a', 'student_b', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('student_a__username', 'student_b__username')

@admin.register(Encouragement)
class EncouragementAdmin(admin.ModelAdmin):
    list_display = ('sender', 'pair', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'pair')

