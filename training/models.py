from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
import datetime

# 1. 练习内容模型 (保持不变)
class Exercise(models.Model):
    title = models.CharField("练习标题", max_length=200)
    content = RichTextUploadingField("练习图文内容", default="")
    demo_audio = models.FileField("示范音频", upload_to='exercise_demos/', blank=True, null=True)
    order = models.IntegerField("排序", default=1)

    def __str__(self):
        return self.title
    class Meta:
        verbose_name = "练习项目"
        verbose_name_plural = "练习项目"

# 2. 每日打卡模型 (保持不变)
class DailyCheckIn(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="学员")
    date = models.DateField("打卡日期", default=datetime.date.today)
    is_submitted = models.BooleanField("是否已提交", default=False)

    # === 新增/修改字段 ===
    teacher_summary = models.TextField("老师文字总评", blank=True, null=True)

    # 新增：老师语音总评
    teacher_audio = models.FileField("老师语音总评", upload_to='teacher_summary/%Y/%m/', blank=True, null=True)

    # 新增：点赞功能 (多对多关联)
    likes = models.ManyToManyField(User, related_name='liked_checkins', blank=True, verbose_name="点赞用户")

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    # 辅助方法：统计点赞数
    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        status = "✅已提交" if self.is_submitted else "📝草稿中"
        return f"[{self.date}] {self.student.username} ({status})"

    class Meta:
        verbose_name = "每日打卡(作业本)"
        verbose_name_plural = "每日打卡(作业本)"
        unique_together = ('student', 'date')

# 3. 练习记录模型 (🔥 修改点：允许录音为空)
class PracticeRecord(models.Model):
    # 关联到每日打卡
    daily_checkin = models.ForeignKey(DailyCheckIn, on_delete=models.CASCADE, verbose_name="所属打卡", related_name="records", null=True, blank=True)

    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="学员")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name="练习项目")

    # 🔥 修改：增加了 blank=True, null=True，允许不上传文件也能保存记录
    student_audio = models.FileField("学员录音", upload_to='student_audios/', blank=True, null=True)

    submitted_at = models.DateTimeField("提交时间", auto_now=True)

    teacher_comment_text = models.TextField("单句点评", blank=True, null=True)
    teacher_comment_audio = models.FileField("语音点评", upload_to='teacher_audios/', blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.exercise.title}"

    class Meta:
        verbose_name = "单条录音"
        verbose_name_plural = "单条录音"

# 4. 公告与阅读记录模型
class Announcement(models.Model):
    title = models.CharField("公告标题", max_length=200)
    content = RichTextUploadingField("公告内容")
    audio_file = models.FileField("语音通知", upload_to='announcement_audios/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField("发布时间", auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="发布人")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "通知公告"
        verbose_name_plural = "通知公告"
        ordering = ['-created_at']

class ReadRecord(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, verbose_name="公告")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="学员")
    read_at = models.DateTimeField("阅读时间", auto_now_add=True)

    class Meta:
        verbose_name = "阅读记录"
        verbose_name_plural = "阅读记录"
        unique_together = ('announcement', 'student')


# ==========================================
# 5. 游戏化系统模型
# ==========================================

class StudentProfile(models.Model):
    """学员游戏化档案"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='game_profile')
    experience_points = models.IntegerField("经验值", default=0)
    level = models.IntegerField("等级", default=1)
    streak_days = models.IntegerField("连续练习天数", default=0)
    last_practice_date = models.DateField("上次练习日期", null=True, blank=True)
    total_practice_days = models.IntegerField("累计练习天数", default=0)
    total_recordings = models.IntegerField("累计录音数", default=0)
    
    def calculate_level(self):
        """根据经验值计算等级: level = floor(sqrt(exp / 100)) + 1"""
        import math
        return int(math.floor(math.sqrt(self.experience_points / 100))) + 1
    
    def update_level(self):
        """更新等级"""
        new_level = self.calculate_level()
        if new_level != self.level:
            self.level = new_level
            self.save()
            return True  # 表示升级了
        return False
    
    def exp_for_next_level(self):
        """下一级所需经验值"""
        return (self.level ** 2) * 100
    
    def exp_progress(self):
        """当前等级进度百分比"""
        current_level_exp = ((self.level - 1) ** 2) * 100
        next_level_exp = (self.level ** 2) * 100
        progress = (self.experience_points - current_level_exp) / (next_level_exp - current_level_exp) * 100
        return min(100, max(0, progress))
    
    def __str__(self):
        return f"{self.user.username} - Lv.{self.level} ({self.experience_points} XP)"
    
    class Meta:
        verbose_name = "学员档案"
        verbose_name_plural = "学员档案"


class Achievement(models.Model):
    """成就定义"""
    CONDITION_TYPES = [
        ('streak', '连续天数'),
        ('total_days', '累计天数'),
        ('exp', '经验值'),
        ('recordings', '录音数量'),
        ('level', '等级'),
        ('first', '首次完成'),
    ]
    
    name = models.CharField("成就名称", max_length=100)
    description = models.TextField("成就描述")
    icon = models.CharField("图标", max_length=50, default="🏆")
    condition_type = models.CharField("条件类型", max_length=50, choices=CONDITION_TYPES)
    condition_value = models.IntegerField("条件值", default=1)
    exp_reward = models.IntegerField("经验奖励", default=50)
    order = models.IntegerField("排序", default=0)
    
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    class Meta:
        verbose_name = "成就"
        verbose_name_plural = "成就"
        ordering = ['order', 'id']


class StudentAchievement(models.Model):
    """学员获得的成就"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField("获得时间", auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.achievement.name}"
    
    class Meta:
        verbose_name = "学员成就"
        verbose_name_plural = "学员成就"
        unique_together = ('student', 'achievement')


# ==========================================
# 6. 互帮系统模型
# ==========================================

class BuddyPair(models.Model):
    """互帮配对"""
    student_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_as_a', verbose_name="学员A")
    student_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_as_b', verbose_name="学员B")
    created_at = models.DateTimeField("配对时间", auto_now_add=True)
    is_active = models.BooleanField("是否有效", default=True)
    
    def get_buddy(self, user):
        """获取伙伴"""
        if user == self.student_a:
            return self.student_b
        elif user == self.student_b:
            return self.student_a
        return None
    
    def __str__(self):
        return f"{self.student_a.username} ↔ {self.student_b.username}"
    
    class Meta:
        verbose_name = "互帮配对"
        verbose_name_plural = "互帮配对"


class Encouragement(models.Model):
    """鼓励消息"""
    pair = models.ForeignKey(BuddyPair, on_delete=models.CASCADE, related_name='encouragements', verbose_name="配对")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="发送者")
    message = models.TextField("鼓励消息", max_length=500)
    created_at = models.DateTimeField("发送时间", auto_now_add=True)
    is_read = models.BooleanField("是否已读", default=False)
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:20]}..."
    
    class Meta:
        verbose_name = "鼓励消息"
        verbose_name_plural = "鼓励消息"
        ordering = ['-created_at']

