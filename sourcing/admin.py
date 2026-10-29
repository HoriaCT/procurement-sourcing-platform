from django.contrib import admin
from .models import Company, UserProfile, RequestForQuotation, Offer


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "company_type", "is_active")
    list_filter = ("company_type", "is_active")
    search_fields = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role")
    list_filter = ("role", "company")


@admin.register(RequestForQuotation)
class RequestForQuotationAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "deadline", "is_open")
    list_filter = ("is_open", "client")
    search_fields = ("title", "description")
    filter_horizontal = ("invited_suppliers",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "request",
        "supplier",
        "price",
        "currency",
        "delivery_days",
        "is_selected",
    )
    list_filter = ("currency", "is_selected")
    search_fields = ("supplier__name", "request__title")
