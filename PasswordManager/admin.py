from django.contrib import admin
from .models import Credential, Note, Role, Permission, CustomUser, UserLog

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

# Register the model with the custom admin class
admin.site.register(Credential, CredentialAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(CustomUser)
