from rest_framework import serializers
from django.contrib.auth import get_user_model
from lms_auth.models import User,UserRole,Role


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
            UserRole.objects.create(
                    user = user,
                    role = role,
                )
        return user
        
    
class RoleSerializer(serializers.ModelSerializer):
    user_set = SignupSerializer(many=True)

    class Meta:
        model = Role
        fields = ["role_type", "user_set"]

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length = 25)
    password = serializers.CharField(style = {"input_type":"password"}, write_only = True)
