from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Assignment, Course, Enrollment, Submission, Topic, UploadStatus
from lms_course.api.permissions import IsActiveMentor, IsCourseOwner, IsEnrolledStudent
from lms_course.api.serializers import *

from lms_course.tasks import send_enrolment_email, send_grade_email, process_topic_material



# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------


class CourseViewSet(viewsets.ModelViewSet):
    """
    Courses endpoint.

    - Any authenticated user: list (title+desc) and retrieve.
    - Active mentors: full CRUD on their own courses.
    - `enrolled_students` action: mentor can list students enrolled in a course.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["creator"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'mentor':
            return Course.objects.filter(creator=user)
        
        return Course.objects.all()
        # return (
        #     Course.objects.select_related("creator")
        #     .prefetch_related("enrollments", "topics")
        #     .all()
        # )

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        if self.action in ("create",):
            return [IsAuthenticated(), IsActiveMentor()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsActiveMentor(), IsCourseOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated, IsActiveMentor],
        url_path="enrolled-students",
    )
    def enrolled_students(self, request, pk=None):
        """Return all students enrolled in this course (mentor only)."""
        course = self.get_object()

        # Ensure requesting mentor owns this course
        if course.creator != request.user:
            return Response(
                {"detail": "You can only view enrollments for your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        enrollments = (
            Enrollment.objects.filter(course=course)
            .select_related("user")
            .order_by("enrolled_at")
        )
        serializer = EnrolledStudentSerializer(enrollments, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------


class TopicViewSet(viewsets.ModelViewSet):
    """
    Topics endpoint.

    - Enrolled students: read-only access to topics of enrolled courses.
    - Active mentors: full CRUD on topics belonging to their own courses.
    - Material upload triggers a background Celery task.
    """

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["course"]

    def get_queryset(self):
        user = self.request.user
        qs = Topic.objects.select_related("course__creator").all()

        # Mentors see topics of their own courses
        if _is_active_mentor(user):
            return qs.filter(course__creator=user)

        return qs.none()

    def get_serializer_class(self):
        if self.request.method in ("GET",):
            return TopicReadSerializer
        return TopicSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsActiveMentor(), IsCourseOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Save topic as PENDING"""
        topic = serializer.save(upload_status=UploadStatus.PENDING)
        if topic.material:
            process_topic_material.delay(topic.pk)

    def perform_update(self, serializer):
        """Re-trigger processing task when material changes."""
        old_material = serializer.instance.material
        topic = serializer.save()
        if topic.material and topic.material != old_material:
            topic.upload_status = UploadStatus.PENDING
            topic.save(update_fields=["upload_status"])
            process_topic_material.delay(topic.pk)

    
    @action(
        detail=False,
        methods=["get"],
        url_path="my-topics",
        permission_classes=[IsAuthenticated],
    )
    def my_topics(self, request):
        user = request.user
        enrolled_course_ids = Enrollment.objects.filter(user=user).values_list(
            "course_id", flat=True
        )
        qs = Topic.objects.select_related("course__creator").filter(
            course_id__in=enrolled_course_ids
        )
        print(qs)
        page = self.paginate_queryset(qs)
        serializer = TopicReadSerializer(
            page or qs, many=True, context={"request": request}
        )
        return (
            self.get_paginated_response(serializer.data)
            if page is not None
            else Response(serializer.data)
        )



# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Assignments endpoint.

    - Enrolled students: read-only.
    - Active mentors: full CRUD on assignments under their topics.
    """

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["topic"]

    def get_queryset(self):
        user = self.request.user
        qs = Assignment.objects.select_related("topic__course__creator").all()

        if _is_active_mentor(user):
            return qs.filter(topic__course__creator=user)

        return qs.none()

    def get_serializer_class(self):
        return AssignmentSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsActiveMentor(), IsCourseOwner()]
        return [IsAuthenticated()]

    @action(
        detail=False,
        methods=["get"],
        url_path="my-assignments",
        permission_classes=[IsAuthenticated],
    )
    def my_assignments(self, request):
        user = request.user
        qs = (
                Assignment.objects.select_related("topic__course")
                .filter(topic__course__enrollments__user=user)
                .exclude(submissions__student=user)
                .distinct()
            )

        page = self.paginate_queryset(qs)
        serializer = AssignmentSerializer(
            page or qs, many=True, context={"request": request}
        )
        return (
            self.get_paginated_response(serializer.data)
            if page is not None
            else Response(serializer.data)
        )

# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------


class SubmissionViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Submissions endpoint.

    - Students: create submission, view own submissions.
    - Mentors: view all submissions for their assignments, grade them.
    """
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["assignment", "student"]

    def get_queryset(self):
        user = self.request.user
        qs = Submission.objects.select_related(
            "assignment__topic__course__creator", "student"
        )

        if _is_active_mentor(user):
            # Mentors see submissions for their assignments only
            return qs.filter(assignment__topic__course__creator=user)

        # Students see only their own submissions
        return qs.none()

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissionCreateSerializer
        if self.action == "grade":
            return SubmissionGradeSerializer
        return SubmissionDetailSerializer

    def get_permissions(self):
        if self.action == "grade":
            return [IsAuthenticated(), IsActiveMentor()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def grade(self, request, pk=None):
        """Grade a student submission (mentor only)."""
        submission = self.get_object()
        

        # Verify mentor owns the course
        if submission.assignment.topic.course.creator != request.user:
            return Response(
                {"detail": "You can only grade submissions in your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        was_ungraded = submission.marks is None
        serializer = SubmissionGradeSerializer(
            submission, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        if was_ungraded and submission.marks is not None:
            student = submission.student
            send_grade_email.delay(
                student_username = student.username,
                student_email = student.email,
                assignment_title = submission.assignment.title,
                marks = submission.marks
            )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="my-submissions",
        permission_classes=[IsAuthenticated],
    )
    def my_submissions(self, request):
        user = request.user
        qs = Submission.objects.select_related(
            "assignment__topic__course__creator", "student"
        ).filter(
            student=user,
            assignment__topic__course__enrollments__user=user
        ).distinct()

        page = self.paginate_queryset(qs)
        serializer = SubmissionDetailSerializer(
            page or qs, many=True, context={"request": request}
        )
        return (
            self.get_paginated_response(serializer.data)
            if page is not None
            else Response(serializer.data)
        )

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------


class EnrollmentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Enrollment endpoint.

    - Students can enroll in (POST) and unenroll from (DELETE) any course.
    - Students can list their own enrollments.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["course"]

    def get_queryset(self):
        return (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course", "user")
            .all()
        )

    def get_serializer_class(self):
        return EnrollmentSerializer
    
    def perform_create(self, serializer):
        send_enrolment_email.delay(
            student_email= self.request.user.email,
            course_title= serializer.validated_data["course"].title,
            student_username= self.request.user.username
        )
        return super().perform_create(serializer)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only unenroll yourself.")
        instance.delete()



def _is_active_mentor(user) -> bool:
    return (
        user.is_authenticated
        and user.userrole_set.filter(role__role_type="mentor", is_active=True).exists()
    )
