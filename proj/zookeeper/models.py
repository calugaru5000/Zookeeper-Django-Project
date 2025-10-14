from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Species(models.Model):
    DIET_CHOICES = [
        ('herbivore', 'Herbivore'),
        ('carnivore', 'Carnivore'),
        ('omnivore', 'Omnivore'),
    ]
    name = models.CharField(max_length=100, unique=True)
    diet = models.CharField(max_length=20, choices=DIET_CHOICES)

    def _str_(self):
        return f"{self.name} ({self.get_diet_display()})"


class Animal(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    enclosure = models.CharField(max_length=100)
    last_fed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.name

    @property
    def needs_feeding(self):
        if not self.last_fed_at:
            return True
        return (timezone.now() - self.last_fed_at).total_seconds() > 24 * 3600