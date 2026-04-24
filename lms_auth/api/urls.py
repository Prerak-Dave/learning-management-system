from django.urls import path,include
from lms_auth.api.views import SignupView, LoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = "user"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signin"),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]