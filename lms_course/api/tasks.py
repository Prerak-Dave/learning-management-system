"""
Celery tasks for the lms_course app.

Handles asynchronous material upload processing.
"""


import time

from lms.celery import shared_task
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def process_topic_material(topic_id):
    """
    Simulates processing an uploaded material file for a Topic.
    Marks the topic as PROCESSING, runs through a few steps, then marks it COMPLETED.
    Triggered from TopicViewSet.perform_create() and perform_update().
    """
   pass


@shared_task
def send_enrollment_email(student_email, student_name, course_title):
    """
    Sends a confirmation email to a student after they enroll in a course.
    Triggered from EnrollmentSerializer.create().
    """
    subject = "Course Enrollment Successful"
    message = (
        f"Hi {student_name},\n\n"
        f"You have successfully enrolled in the course: {course_title}.\n\n"
        f"We hope you enjoy learning!\n\n"
        f"Regards,\nThe LMS Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[student_email],
        fail_silently=True,  # don't crash the app if SMTP is misconfigured
    )


@shared_task
def send_grade_email(student_email, student_name, assignment_title, marks):
    """
    Sends a grade notification email to a student after their submission is graded.
    Triggered from SubmissionViewSet.grade().
    """
    subject = "Assignment Graded"
    message = (
        f"Hi {student_name},\n\n"
        f"Your assignment '{assignment_title}' has been graded.\n"
        f"Marks obtained: {marks}\n\n"
        f"Keep up the good work!\n\n"
        f"Regards,\nThe LMS Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[student_email],
        fail_silently=True,
    )
