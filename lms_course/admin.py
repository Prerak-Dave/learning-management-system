from django.contrib import admin
from lms_course.models import Course,Topic,Assignment,Enrollment

admin.site.register([Course, Topic, Assignment, Enrollment])
