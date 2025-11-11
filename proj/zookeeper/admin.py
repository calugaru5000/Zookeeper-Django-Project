from django.contrib import admin
from .models import Species, Animal, Enclosure, StaffRole

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("name", "diet")
    search_fields = ("name",)

@admin.register(Enclosure)
class EnclosureAdmin(admin.ModelAdmin):
    list_display = ("name", "diet_type", "capacity", "current_occupancy", "created_at")
    list_filter = ("diet_type", "created_at")
    search_fields = ("name",)

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "enclosure", "owner", "last_fed_at", "created_at")
    list_filter = ("species", "enclosure", "created_at")
    search_fields = ("name",)

@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "enclosure", "role", "assigned_at", "assigned_by")
    list_filter = ("role", "enclosure", "assigned_at")
    search_fields = ("user__username", "enclosure__name")
    readonly_fields = ("assigned_at",)
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new StaffRole
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)