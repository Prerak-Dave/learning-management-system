from django.db import models
from django.contrib.auth.models import AbstractUser
from multiselectfield import MultiSelectField

class Role(models.Model):
    role_type = models.CharField(max_length=15)

    def __str__(self):
        return self.role_type
    
class User(AbstractUser):
    role = models.ManyToManyField(Role, through='UserRole')

    def __str__(self):
        return self.username

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} -> {self.role}"

class StudentProfile(models.Model):
    interests_choices = (
        ('1','Java'),
        ('2','Python'),
        ('3','SQL'),
        ('4','MongoDB'),
        ('5','Django'),
        ('6','HTML/CSS'),
        ('7','Node.js'),
        ('8','FAST-API'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interests = MultiSelectField(
        choices= interests_choices,
        default=['2']
    )

class MentorProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=300)
    resume = models.FileField(upload_to='lms_auth/')