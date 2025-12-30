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
