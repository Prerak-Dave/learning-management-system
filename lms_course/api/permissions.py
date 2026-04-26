"""
Custom DRF permission classes for the lms_course app.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_active_mentor(user) -> bool:
    """Return True if *user* has an active Mentor role."""
    return (
        user.is_authenticated
        and user.user_roles.filter(
            role__name="Mentor", is_active=True
        ).exists()
    )


class IsActiveMentor(BasePermission):
    """Allow access only to users with an active Mentor role."""

    message = "You must be an active mentor to perform this action."

    def has_permission(self, request, view) -> bool:
        return _is_active_mentor(request.user)


class IsActiveMentorOrReadOnly(BasePermission):
    """
    Read access for everyone authenticated;
    write access only for active mentors.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return _is_active_mentor(request.user)


class IsCourseOwner(BasePermission):
    """
    Object-level: allow writes only to the mentor who created the course
    (or a course that belongs to a resource owned by them).
    """

    message = "You can only modify your own courses."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        # obj may be Course, Topic, Assignment, or Submission
        course = _resolve_course(obj)
        return course is not None and course.creator == request.user


class IsEnrolledStudent(BasePermission):
    """Allow access only if the requesting student is enrolled in the course."""

    message = "You must be enrolled in this course to access its content."

    def has_object_permission(self, request, view, obj) -> bool:
        from lms_course.models import Enrollment  # local import to avoid circular

        course = _resolve_course(obj)
        if course is None:
            return False
        return Enrollment.objects.filter(
            user=request.user, course=course
        ).exists()


class IsSubmissionOwner(BasePermission):
    """Students may only access their own submissions."""

    message = "You can only access your own submissions."

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.student == request.user


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _resolve_course(obj):
    """Walk relationships to find the parent Course of any LMS object."""
    from lms_course.models import Course, Topic, Assignment, Submission, Enrollment

    if isinstance(obj, Course):
        return obj
    if isinstance(obj, Topic):
        return obj.course
    if isinstance(obj, Assignment):
        return obj.topic.course
    if isinstance(obj, Submission):
        return obj.assignment.topic.course
    if isinstance(obj, Enrollment):
        return obj.course
    return None
