from rest_framework.views import APIView
from lms_auth.api.serializers import SignupSerializer
from rest_framework.response import Response 

class SignupView(APIView):
    def post(self,request):
        serializer = SignupSerializer(data = request.data)
        data = {}
        if serializer.is_valid():
            user = serializer.save()
            data['response'] = "User successfully created"
            data['email'] = user.email
            data['username'] = user.username
            data['role'] = user.role
        else:
            data = serializer.errors
        
        return Response(data)
