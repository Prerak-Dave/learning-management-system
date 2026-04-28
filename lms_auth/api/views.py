from rest_framework.views import APIView
from lms_auth.api.serializers import SignupSerializer, LoginSerializer
from rest_framework.response import Response 
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

class SignupView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = SignupSerializer(data = request.data)
        data = {}
        if serializer.is_valid():
            user = serializer.save()
            data['response'] = "User successfully created"
            data['email'] = user.email
            data['username'] = user.username
            data['role'] = [role.role_type for role in user.role.all()]
        else:
            data = serializer.errors
        
        return Response(data)
    
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer