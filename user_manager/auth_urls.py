from django.urls import path
from .view.auth_view import LoginView, VerifyTokenView, LogoutView, ChangePasswordView

app_name = 'auth'

urlpatterns = [
    # Authentication endpoints (when accessed via /api/auth/)
    path('login/', LoginView.as_view(), name='login'),
    path('verify/', VerifyTokenView.as_view(), name='verify_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('<uuid:user_uuid>/change-password/', ChangePasswordView.as_view(), name='change_password'),
]