"""
Serializers for the lms_course app.
"""

from django.utils import timezone
from rest_framework import serializers

from lms_course.models import Assignment, Course, Enrollment, Submission, Topic


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for student course browsing (title + description)."""
    creator_name = serializers.CharField(source='creator.username', read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "description", "start_date","creator_name"]


class CourseDetailSerializer(serializers.ModelSerializer):
    """Full course detail used by mentors and enrolled students."""

    creator_username = serializers.CharField(source="creator.username", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "creator",
            "creator_username",
            "created_at",
            "updated_at",
            ]
        read_only_fields = ["creator", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------


class TopicSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Topic
        fields = [
            "id",
            "course",
            "title",
            "material",
            "thumbnail",
            "upload_status",
            "created_at",
            ]
        read_only_fields = ["upload_status", "created_at", "course_title",]

    def validate_course(self, course):
        """Mentor may only add topics to their own courses."""
        request = self.context["request"]
        if course.creator != request.user:
            raise serializers.ValidationError("You can only add topics to your own courses.")
        return course


class TopicReadSerializer(serializers.ModelSerializer):
    """Serializer used when reading topics (students)."""
    course_title = serializers.CharField(source = 'course.title', read_only = True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "course",
            "title",
            "material",
            "thumbnail",
            "course_title",
            "upload_status",
        ]
        read_only = True


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


class AssignmentSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    course_title = serializers.CharField(source="topic.course.title", read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id",
            "topic",
            "title",
            "description",
            "created_at",
            "topic_title",
            "course_title",
        ]
        read_only_fields = ["created_at", "topic_title","course_title"]

    def validate_topic(self, topic):
        """Mentor may only manage assignments in topics they own."""
        request = self.context["request"]
        if topic.course.creator != request.user:
            raise serializers.ValidationError("You can only manage assignments for your own topics.")
        return topic


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Used by students to create a submission."""

    class Meta:
        model = Submission
        fields = ["id", "assignment", "file", "submitted_at"]
        read_only_fields = ["submitted_at"]

    def validate_assignment(self, assignment):
        """
        Ensure the student is enrolled in the course that owns this assignment,
        and has not already submitted.
        """
        request = self.context["request"]
        course = assignment.topic.course

        enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        if not enrolled:
            raise serializers.ValidationError(
                "You must be enrolled in this course to submit assignments."
            )

        already_submitted = Submission.objects.filter(assignment=assignment, student=request.user).exists()
        if already_submitted:
            raise serializers.ValidationError("You have already submitted for this assignment.")

        return assignment

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)


class SubmissionGradeSerializer(serializers.ModelSerializer):
    """Used by mentors to grade a submission."""

    class Meta:
        model = Submission
        fields = ["id", "marks", "graded_at"]
        read_only_fields = ["graded_at"]

    def update(self, instance, validated_data):
        instance.marks = validated_data.get("marks", instance.marks)
        instance.graded_at = timezone.now()
        instance.save()
        return instance


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Read-only detail view of a submission."""
    student_username = serializers.CharField(
        source="student.username", read_only=True
    )
    assignment_title = serializers.CharField(
        source="assignment.title", read_only=True
    )
    assignment_description = serializers.CharField(
        source="assignment.description", read_only=True
    )
    topic_title = serializers.CharField(
        source="assignment.topic.title", read_only=True
    )
    course_title = serializers.CharField(
        source="assignment.topic.course.title", read_only=True
    )

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "assignment_title",
            "assignment_description",
            "topic_title",
            "course_title",
            "student",
            "student_username",
            "file",
            "marks",
            "submitted_at",
            "graded_at",
        ]


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source = 'course.title', read_only = True)
    class Meta:
        model = Enrollment
        fields = ["id", "user", "course", "enrolled_at", "course_title"]
        read_only_fields = ["user", "enrolled_at", "course_title"]

    def validate_course(self, course):
        request = self.context["request"]
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")
        return course

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class EnrolledStudentSerializer(serializers.ModelSerializer):
    """Used by mentors to list students enrolled in their course."""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "user", "username", "email", "enrolled_at"]