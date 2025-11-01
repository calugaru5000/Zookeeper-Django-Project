from django.contrib import admin
from .models import Species, Animal, Enclosure

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