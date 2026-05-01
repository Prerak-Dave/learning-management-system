"""
Celery tasks for the lms_course app.

Handles asynchronous material upload processing.
"""

import time

from celery import shared_task
from django.core.mail import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# Allowed file types and size limit
ALLOWED_EXTENSIONS = {".pdf", ".mp4", ".mov", ".png"}
MAX_FILE_SIZE_MB = 15
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 15MB in bytes
 
 
@shared_task
def process_topic_material(topic_id):
    """
    Validates and processes an uploaded material file for a Topic.
 
    Checks:
        1. File must be a .pdf, .mp4, or .mov
        2. File must not exceed 15MB
 
    Marks topic.upload_status as:
        - PROCESSING while running
        - COMPLETED if all checks pass
        - FAILED if any check fails (with a reason logged)
 
    Triggered from TopicViewSet.perform_create() and perform_update().
    """
    import os
    # Imported inside the function so this module loads before Django is fully ready
    from lms_course.models import Topic, UploadStatus
 
    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return {"status": "error", "topic_id": topic_id}
 
    # Mark as PROCESSING so the API can show a "processing" state
    topic.upload_status = UploadStatus.PROCESSING
    topic.save(update_fields=["upload_status"])
 
    try:
        # ── Step 1: Check file extension ──────────────────────────────────
        # os.path.splitext splits "lecture.pdf" into ("lecture", ".pdf")
        _, extension = os.path.splitext(topic.material.name)
        extension = extension.lower()  # normalize: ".PDF" → ".pdf"
 
        if extension not in ALLOWED_EXTENSIONS:
            topic.upload_status = UploadStatus.FAILED
            topic.save(update_fields=["upload_status"])
            return {
                "status": "failed",
                "topic_id": topic_id,
                "reason": f"Invalid file type '{extension}'. Only PDF, MP4, and MOV are allowed.",
            }
 

        # ── Step 2: Check file size ───────────────────────────────────────
        # topic.material.size gives the file size in bytes directly from the FileField
        file_size_bytes = topic.material.size
        file_size_mb = file_size_bytes / (1024 * 1024)
 
        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            topic.upload_status = UploadStatus.FAILED
            topic.save(update_fields=["upload_status"])
            return {
                "status": "failed",
                "topic_id": topic_id,
                "reason": f"File size {file_size_mb:.2f}MB exceeds the {MAX_FILE_SIZE_MB}MB limit.",
            }
 
        topic.upload_status = UploadStatus.COMPLETED
        topic.save(update_fields=["upload_status"])
        return {"status": "completed", "topic_id": topic_id}
 
    except Exception as e:
        topic.upload_status = UploadStatus.FAILED
        topic.save(update_fields=["upload_status"])
        return {"status": "failed", "topic_id": topic_id, "reason": str(e)}
    

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
    