"""
Models for the lms_course app.

Covers: Course, Topic, Assignment, Submission, Enrollment.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone



class UploadStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class Course(models.Model):
    """A course created by a mentor."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField(auto_now_add=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_courses",)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["creator"])]

    def __str__(self) -> str:
        return self.title


class Topic(models.Model):
    """A topic belonging to a course, optionally with material and thumbnail."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=255)
    material = models.FileField(upload_to="media/videos/")
    thumbnail = models.ImageField(upload_to="media/thumbnails/")
    upload_status = models.CharField(max_length=20, choices=UploadStatus.choices, default=UploadStatus.PENDING,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["course"])]

    def __str__(self) -> str:
        return f"{self.course.title} - {self.title}"


class Assignment(models.Model):
    """An assignment attached to a topic."""    

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["topic"])]

    def __str__(self) -> str:
        return self.title


class Submission(models.Model):
    """
    A student's file submission for an assignment.

    One submission per (assignment, student) pair — enforced at DB and
    serializer level.
    """

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="submissions",)
    file = models.FileField(upload_to="media/sumbmissions/")
    marks = models.IntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("assignment", "student")]
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["assignment"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.assignment}"


class Enrollment(models.Model):
    """Tracks which student is enrolled in which course."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="enrollments",)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "course")]
        ordering = ["-enrolled_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["course"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} enrolled in {self.course}"

