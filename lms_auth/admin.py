from django.contrib import admin
from django.contrib.auth import get_user_model
from lms_auth.models import Role,UserRole

admin.site.register(get_user_model())
admin.site.register([Role, UserRole])

# Register your models here.
