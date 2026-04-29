"""
Celery tasks for the lms_course app.

Handles asynchronous material upload processing.
"""

import time

from celery import shared_task
from django.core.mail import EmailMessage
from dotenv import load_dotenv

load_dotenv()


@shared_task(bind = True)
def process_topic_material(self, topic_id: int) -> dict:
    """
    Process an uploaded material file for a Topic.
    """
    # Defer model import so the task module is importable before Django is ready
    from lms_course.models import Topic, UploadStatus


    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return {"status": "error", "topic_id": topic_id, "detail": "Topic not found"}

    # Mark as PROCESSING
    topic.upload_status = UploadStatus.PROCESSING
    topic.save(update_fields=["upload_status"])

    try:
        pass
    except:
        topic.upload_status = UploadStatus.FAILED
        topic.save(update_fields=["upload_status"])


@shared_task
def send_enrolment_email(course_title, student_username, student_email):
    email = EmailMessage(
        subject="Enrollment mail",
        body=
        f"""Hey {student_username},
        You recently enrolled for course: {course_title}.
        Regards,
        Team LMS""",
        to= (student_email,)
    )

    return email.send()

@shared_task
def send_grade_email(assignment_title, student_username, marks, student_email):
    email = EmailMessage(
        subject=f"Grade Recieved for : {assignment_title}",
        body=
        f"""Hey {student_username},
        You have been awarded {marks} for {assignment_title}.
        Regards,
        Team LMS""",
        to= (student_email,)
    )

    return email.send()
    