"""
URL configuration for lms_course.

All routes are registered via DRF's DefaultRouter.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from lms_course.views import (
    AssignmentViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    SubmissionViewSet,
    TopicViewSet,
)

router = DefaultRouter()
router.register(r"topics", TopicViewSet, basename="topic")
router.register(r"assignments", AssignmentViewSet, basename="assignment")
router.register(r"submissions", SubmissionViewSet, basename="submission")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")
router.register(r"", CourseViewSet, basename="course") # detail view: /<pk : int> , list view: / , up

urlpatterns = [
    path("", include(router.urls)),
]