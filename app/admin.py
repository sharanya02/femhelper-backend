from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ChatRoom, Messages, Alert
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        "email",
        "username",
        "phone_no",
        "date_of_birth",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "email",
        "username",
        "phone_no",
        "date_of_birth",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (
            None,
            {"fields": ("email", "username", "phone_no", "date_of_birth", "password")},
        ),
        ("Permissions", {"fields": ("is_staff", "is_active")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "phone_no",
                    "date_of_birth",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email", "username", "phone_no")
    ordering = ("email", "username", "phone_no")


admin.site.register(User, CustomUserAdmin)
admin.site.register(ChatRoom)
admin.site.register(Messages)
admin.site.register(Alert)
