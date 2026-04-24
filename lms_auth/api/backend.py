from django.contrib.auth.backends import ModelBackend

class CustomBackend(ModelBackend):
    def authenticate(self, request, username = ..., password = ..., **kwargs):
        role_id = kwargs.get('role')
        user = super().authenticate(request, username, password)
        if user is None:
            return None
        if role_id is None:
            return None
        user_role = user.userrole_set.filter(
                    role_id=role_id,
                    is_active=True
                    ).first()

        if not user_role:
            return None
        return user