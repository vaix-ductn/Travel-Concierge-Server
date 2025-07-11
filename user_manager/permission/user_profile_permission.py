from base.permission.rest_framework.view_set import ViewSetPermission

class UserProfilePermission(ViewSetPermission):
    @property
    def for_model(self):
        return ['user_manager', 'UserProfile']
    @property
    def field_name(self):
        return 'user_profile_uuid'
    def has_all_permission(self, request):
        # Cho phép tất cả, có thể mở rộng logic phân quyền tại đây
        return True