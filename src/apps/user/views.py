from src.apps.user.serializers import UserSerializer, UserEditSerializer
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from src.api.utils import generar_codigo
from src.apps.user.models import User
from src.shared.views.base_view import BaseModelViewSet


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        try:
            with transaction.atomic():
                user = User.objects.filter(
                    email=request.data.get("email", None))
                if user.count() > 0:
                    return Response(
                        {"message": "Este correo ya esta en uso"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                user.set_password(user.password)
                user.save()
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = User.objects.get(id=kwargs["pk"])
                serializer = UserEditSerializer(
                    data=request.data, instance=instance, partial=True
                )
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def admin_create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = User.objects.filter(
                    is_staff=True,
                    email=request.data.get("email", None))
                if user.count() > 0:
                    return Response(
                        {"message": "Este correo ya esta en uso"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = User.objects.filter(
                    is_staff=False,
                    email=request.data.get("email", None))
                if user.count() > 0:
                    user_aux = User.objects.get(
                        email=request.data.get('email', None))
                    user_aux.is_staff = True
                    user_aux.save()
                    return Response(UserSerializer(user_aux).data)
                else:
                    serializer = self.serializer_class(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    user = serializer.save()
                    user.set_password(user.password)
                    user.save()
                    return Response(serializer.data)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        serializer = AuthTokenSerializer()
        try:
            serializer: AuthTokenSerializer = AuthTokenSerializer(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user"]
            user.set_password(request.data.get("new_password", None))
            user.save()
            return Response(
                {
                    "message": "La contraseña se ha cambiado satisfactoriamente",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    "message": "Contraseña incorrecta. Revise los datos introducidos",
                    "errors": serializer.errors,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


# Create your views here.
class AuthViewSet(viewsets.ViewSet):
    serializer_class = AuthTokenSerializer

    @action(detail=False, methods=['post'])
    def login(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer()
        try:
            serializer = self.serializer_class(data=request.data,
                                               context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            user.restore_code = None
            user.save()
            return Response({
                'token': str(refresh.access_token),
                'token_refresh': str(refresh),
                'user': UserSerializer(user).data,
            })
        except Exception as e:
            return Response({
                'message': 'Wrong username or password. Check the data entered',
                'errors': serializer.errors
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def sending_restore_code(self, request):
        try:
            user = User.objects.get(email=request.data.get('email', None))
            user.restore_code = generar_codigo()
            user.save()
            text_content = f''' 
              <span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;; font-size: medium;">Dear {user.first_name} {user.last_name},&nbsp;</span><div><font color="#000000" face="Times New Roman" size="3"><br></font><div><span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;; font-size: medium;">We are sending you this email in response to your password reset request.&nbsp;</span></div><div><span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;;"><font size="3">Your verification code is </font><b style=""><font size="4">{user.restore_code}</font></b><font size="3">. Please enter this code on the password reset page to proceed with the password reset process. If you did not request a password reset, please ignore this message.</font></span></div><div><span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;;"><font size="3">Thank you.</font></span></div><div style="text-align: left;"><span style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;;"><font size="3">ARTESSE PROJECT</font></span></div></div>
              '''
            # sendMail.delay({
            #     'subject': 'Restore password',
            #     'text_content': text_content,
            #     'to': request.data.get("email", None),
            #     'html_content': text_content
            # })
            return Response({
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'error': "Email does not exist"
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def restore_password(self, request):
        try:
            user = User.objects.get(id=request.data.get('user_id', None))
            if str(user.restore_code) == str(request.data.get('code', None)):
                user.set_password(request.data.get("new_password", None))
                user.save()
                return Response()
            else:
                return Response({
                    'error': 'This code is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'error': "Email does not exist"
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def register(self, request, *arg, **kwargs):
        try:
            with transaction.atomic():
                user = User.objects.filter(
                    email=request.data.get("email", None))
                if user.count() > 0:
                    return Response(
                        {"message": "This email is already in use"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                serializer = UserSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                user.set_password(user.password)
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'token': str(refresh.access_token),
                    'token_refresh': str(refresh),
                    'user': UserSerializer(user).data,
                })
        except Exception as e:
            print(e)
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
