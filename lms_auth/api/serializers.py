from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from lms_auth.models import User,UserRole,Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class SignupSerializer(serializers.ModelSerializer):
   
    password2 = serializers.CharField(style = {"input_type" : "password"}, write_only = True)
    role = serializers.PrimaryKeyRelatedField(queryset = Role.objects.all(),many = True)
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'password2', 'role']
        extra_kwargs = {
            "password" : {'write_only' : True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password":"Both the passwords should match"})
        return attrs

    def create(self, validated_data):
        roles = validated_data.pop('role')
        validated_data.pop('password2')

        user = User(
            username = validated_data['username'],
            email = validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        
        for role in roles:
            is_active = False
            if role.role_type == "student":
                is_active = True
            print(f"role: {role}, is_active: {is_active}")
            UserRole.objects.create(
                    user = user,
                    role = role,
                    is_active = is_active,
                )
        return user
        
    

class LoginSerializer(TokenObtainPairSerializer):
    """
    Serializer class to authenticate users with username, password and role.
    """ 
    role = serializers.IntegerField(write_only = True)

    def validate(self, attrs):
        role_id = attrs.pop('role')
        print(f"role id : {role_id}")
        user = authenticate(
            username = attrs.get('username'),
            password = attrs.get('password'),
            role = role_id
        )
        if user is None:
            raise serializers.ValidationError("User doesn't exist or role not active!")
        
        data = super().get_token(user)

        return {
            "refresh" : str(data),
            "access" : str(data.access_token),
        }