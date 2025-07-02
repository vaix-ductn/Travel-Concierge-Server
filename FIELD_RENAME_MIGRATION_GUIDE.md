# 🔄 Field Rename Migration Guide: `id` → `profile_uuid`

## Overview
Comprehensive guide for migrating the UserProfile model's primary key field from `id` to `profile_uuid` across the entire Travel Concierge system.

## 📋 **Changes Summary**

### 1. Database Schema Changes
- **Field Rename**: `id` → `profile_uuid`
- **Table**: `user_profiles`
- **Type**: UUID4 (unchanged)
- **Primary Key**: Maintained

### 2. Model Updates
**File**: `user_manager/models.py`
```python
# Before
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# After
profile_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
```

### 3. API Endpoint Changes
**File**: `user_manager/urls.py`
```python
# Before
path('profile/<uuid:profile_id>/', views.get_user_profile)

# After
path('profile/<uuid:profile_uuid>/', views.get_user_profile)
```

### 4. View Function Updates
**File**: `user_manager/views.py`
- All view functions now use `profile_uuid` parameter
- Database queries use `profile_uuid=profile_uuid`
- Log messages updated to show UUID instead of ID

### 5. API Response Changes
```json
{
  "success": true,
  "data": {
    "profile_uuid": "87654321-4321-4321-4321-210987654321",
    "username": "nero",
    "email": "tranamynero@gmail.com"
  }
}
```

## 🔧 **Migration Process**

### Step 1: Update Model
```python
class UserProfile(models.Model):
    profile_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ... other fields
```

### Step 2: Update Serializers
```python
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        read_only_fields = ['profile_uuid', 'created_at', 'updated_at']
```

### Step 3: Update Views
```python
def get_user_profile(request, profile_uuid):
    profile = get_object_or_404(UserProfile, profile_uuid=profile_uuid)
```

### Step 4: Update URLs
```python
path('profile/<uuid:profile_uuid>/', views.get_user_profile, name='get_profile')
```

### Step 5: Database Migration
```bash
# Manual migration using script
docker-compose run web python migrate_profile_uuid.py

# Or Django migration (if working)
docker-compose run web python manage.py migrate user_manager
```

## 📡 **API Endpoint Changes**

### Before (profile_id)
```bash
GET /api/user_manager/profile/{profile_id}/
PUT /api/user_manager/profile/{profile_id}/update/
PUT /api/user_manager/profile/{profile_id}/change-password/
```

### After (profile_uuid)
```bash
GET /api/user_manager/profile/{profile_uuid}/
PUT /api/user_manager/profile/{profile_uuid}/update/
PUT /api/user_manager/profile/{profile_uuid}/change-password/
```

## 🧪 **Testing Changes**

### Updated Test Cases
```python
def test_get_profile_api(self):
    url = reverse('user_manager:get_profile', kwargs={'profile_uuid': self.profile.profile_uuid})
    response = self.client.get(url)
    self.assertEqual(response.data['profile_uuid'], str(self.profile.profile_uuid))
```

### URL Resolution Tests
```python
def test_profile_urls_resolve(self):
    url = reverse('user_manager:get_profile', kwargs={'profile_uuid': self.profile.profile_uuid})
    expected = f'/api/user_manager/profile/{self.profile.profile_uuid}/'
    self.assertEqual(url, expected)
```

## 📝 **Documentation Updates**

### Files Updated:
1. **API_TESTING_GUIDE.md** - All curl examples updated
2. **SEED_DATA_README.md** - API examples updated
3. **user_manager/tests.py** - All test cases updated
4. **Manual migration script** - `migrate_profile_uuid.py` created

### Key Documentation Changes:
- All `{profile_id}` → `{profile_uuid}`
- All `Profile ID` → `Profile UUID`
- Log messages updated
- Error messages updated

## 🚀 **Deployment Steps**

### 1. Code Deployment
```bash
# Pull latest changes
git pull origin main

# No container rebuild needed (Python code changes only)
docker-compose restart web
```

### 2. Database Migration
```bash
# Option A: Manual script (recommended)
docker-compose run web python migrate_profile_uuid.py

# Option B: Django migrations (if working)
docker-compose run web python manage.py migrate user_manager
```

### 3. Verification
```bash
# Test API endpoints
curl -X GET "http://localhost:8001/api/user_manager/profiles/"

# Verify field name in response
curl -X GET "http://localhost:8001/api/user_manager/profile/{profile_uuid}/" | jq '.data.profile_uuid'
```

## ⚠️ **Breaking Changes**

### Client Applications
- **API Parameter**: `profile_id` → `profile_uuid`
- **Response Field**: `id` → `profile_uuid`
- **URL Structure**: Same format, different parameter name

### Migration Impact
- **No Data Loss**: Field rename preserves all data
- **UUID Values**: Remain identical (only field name changes)
- **Indexes**: Automatically updated by database

## 📊 **Before vs After Comparison**

| Aspect | Before | After |
|--------|--------|-------|
| **Model Field** | `id` | `profile_uuid` |
| **URL Parameter** | `<uuid:profile_id>` | `<uuid:profile_uuid>` |
| **View Parameter** | `profile_id` | `profile_uuid` |
| **Database Query** | `id=profile_id` | `profile_uuid=profile_uuid` |
| **JSON Response** | `"id": "uuid..."` | `"profile_uuid": "uuid..."` |
| **Log Messages** | `Profile ID: {id}` | `Profile UUID: {uuid}` |

## 🔍 **Verification Checklist**

### Database Level
- [ ] `user_profiles` table has `profile_uuid` field
- [ ] No `id` field exists in `user_profiles` table
- [ ] Primary key constraint maintained
- [ ] All existing data preserved

### API Level
- [ ] GET `/profiles/` returns `profile_uuid` field
- [ ] GET `/profile/{uuid}/` accepts profile_uuid parameter
- [ ] PUT `/profile/{uuid}/update/` works with profile_uuid
- [ ] PUT `/profile/{uuid}/change-password/` works with profile_uuid
- [ ] POST `/profile/create/` returns `profile_uuid` in response

### Code Level
- [ ] All imports and references updated
- [ ] Tests pass with new field name
- [ ] No remaining `profile_id` references in code
- [ ] Logs show `Profile UUID` instead of `Profile ID`

### Documentation Level
- [ ] API guide updated with new parameter names
- [ ] Seed data guide updated
- [ ] All curl examples use `profile_uuid`
- [ ] README files reflect changes

## 🚨 **Rollback Plan**

If issues occur, rollback by:

### 1. Revert Code Changes
```bash
git checkout HEAD~1 -- user_manager/
```

### 2. Revert Database (if needed)
```sql
ALTER TABLE user_profiles RENAME COLUMN profile_uuid TO id;
```

### 3. Restart Services
```bash
docker-compose restart web
```

## 💡 **Best Practices Applied**

1. **Backward Compatibility**: UUID values preserved
2. **Comprehensive Testing**: All test cases updated
3. **Documentation**: Complete API documentation updated
4. **Manual Migration**: Created for complex scenarios
5. **Verification**: Multiple verification methods provided
6. **Rollback Plan**: Clear rollback procedure documented

## 📚 **Related Files**

### Primary Files Modified:
- `user_manager/models.py`
- `user_manager/views.py`
- `user_manager/urls.py`
- `user_manager/serializers.py`
- `user_manager/tests.py`

### Documentation Updated:
- `API_TESTING_GUIDE.md`
- `SEED_DATA_README.md`
- `FIELD_RENAME_MIGRATION_GUIDE.md` (this file)

### Migration Files:
- `user_manager/migrations/0002_rename_id_to_profile_uuid.py`
- `migrate_profile_uuid.py` (manual script)

---

**✅ Migration Complete**: The system now uses `profile_uuid` consistently across all components for better semantic clarity and API consistency.