from django.contrib import admin
from .models import Credential, Note, Role, Permission, CustomUser, UserLog, ScopedToken, EmergencyAccessCode

# admin.site.register(Credential)
# admin.site.register(Note)

class CredentialAdmin(admin.ModelAdmin):
    list_display = ('website_name', 'username', 'email', 'url', 'logo')  # which columns show up in the table
    search_fields = ('website_name', 'email') # adding a search bar to the top of the admin page
    list_filter = ('website_name',) # adds a filter sidebar

class NoteAdmin(admin.ModelAdmin):
    list_display = ('headline', 'bodytext')  # which columns show up in the table
    search_fields = ('headline', 'bodytext') # adding a search bar to the top of the admin page
    list_filter = ('headline',)

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'action', 'timestamp', 'is_suspicious')

@admin.register(ScopedToken)
class ScopedTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'scope', 'token', 'expires_at', 'is_revoked')
    list_filter = ('scope', 'is_revoked')
    search_fields = ('user__username', 'token')


@admin.register(EmergencyAccessCode)
class EmergencyAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_truncated_hash', 'used')
    list_filter = ('used',)
    search_fields = ('user__username',)

    def get_truncated_hash(self, obj):
        if obj.code_hash:
            return f"{obj.code_hash[:20]}..."
        return "-"
    get_truncated_hash.short_description = "Code Hash"


# Register the model with the custom admin class
admin.site.register(Credential, CredentialAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(CustomUser)
