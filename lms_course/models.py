from django.db import models
from lms_auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=50, null=False, blank=False)
    desc = models.TextField(max_length=200)
    start_date = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

class Topic(models.Model):
    title = models.CharField(max_length=50, null=False, blank=False)
    material = models.FileField(upload_to="media/videos/")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    thumbnail = models.FileField(upload_to="media/thumbnails/")

class Assignment(models.Model):
    title = models.CharField(max_length=50, null=False, blank=False)
    desc = models.TextField(max_length=200)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assignment = models.OneToOneField(Assignment, on_delete= models.CASCADE)
    submission_file = models.FileField(upload_to="media/submissions/") 

