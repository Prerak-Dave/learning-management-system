"""
Celery tasks for the lms_course app.

Handles asynchronous material upload processing.
"""

import time

from celery import shared_task



# @shared_task(bind=True, max_retries=3, default_retry_delay=10)
# def process_topic_material(self, topic_id: int) -> dict:
#     """
#     Process an uploaded material file for a Topic.

#     Steps:
#         1. Mark topic as PROCESSING.
#         2. Simulate file processing (e.g., virus scan, format conversion).
#         3. Update progress incrementally.
#         4. Mark as COMPLETED (or FAILED on error).

#     Args:
#         topic_id: PK of the Topic whose material should be processed.

#     Returns:
#         dict with status and topic_id.
#     """
#     # Defer model import so the task module is importable before Django is ready
#     from lms_course.models import Topic, UploadStatus


#     try:
#         topic = Topic.objects.get(pk=topic_id)
#     except Topic.DoesNotExist:
#         return {"status": "error", "topic_id": topic_id, "detail": "Topic not found"}

#     # Mark as PROCESSING
#     topic.upload_status = UploadStatus.PROCESSING
#     topic.upload_progress = 0
#     topic.save(update_fields=["upload_status", "upload_progress"])

#     try:
#         # ------------------------------------------------------------------ #
#         # Simulated processing pipeline                                        #
#         # Replace each step with real logic (e.g., boto3 upload, ffmpeg, ...) #
#         # ------------------------------------------------------------------ #
#         steps = [
#             ("Validating file format", 20),
#             ("Scanning for malware", 40),
#             ("Generating preview", 60),
#             ("Optimising storage", 80),
#             ("Finalising", 100),
#         ]

#         for description, progress in steps:
#             time.sleep(1)  # simulate I/O-bound work
#             topic.upload_progress = progress
#             topic.save(update_fields=["upload_progress"])

#         topic.upload_status = UploadStatus.COMPLETED
#         topic.save(update_fields=["upload_status"])
#         return {"status": "completed", "topic_id": topic_id}

#     except Exception as exc:
#         topic.upload_status = UploadStatus.FAILED
#         topic.save(update_fields=["upload_status"])

#         # Retry with exponential back-off
#         raise self.retry(exc=exc)

@shared_task
def send_enrolment_email(self,):
    pass