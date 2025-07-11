from base.permission.rest_framework.view_set import ViewSetPermission

class AuthPermission(ViewSetPermission):
    @property
    def for_model(self):
        return ['user_manager', 'User']
    @property
    def field_name(self):
        return 'user_uuid'
    def has_all_permission(self, request):
        # Cho phép tất cả, có thể mở rộng logic phân quyền tại đây
        return True