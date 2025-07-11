from django.contrib import admin

from .models import CustomUser,UserProfile,AllowedEmailDomain


admin.site.register(UserProfile)
admin.site.register(AllowedEmailDomain)



class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "user_department", "user_position")

admin.site.register(CustomUser, CustomUserAdmin)
