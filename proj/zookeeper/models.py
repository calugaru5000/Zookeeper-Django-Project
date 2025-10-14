from django.db import models

class Species(models.Model):
    DIETS = [
        ("herbivore","Herbivore"),
        ("carnivore", "Carnivore"),
        ("omnivore", "Omnivore"),
    ]
    name = models.CharField(max_length=100)
    diet = models.CharField(max_length=10, choices=DIETS)
    def __str__(self): return f"{self.name} ({self.get_diet_display()})"

class Animal(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    enclosure = models.CharField(max_length=100)
    last_fed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name