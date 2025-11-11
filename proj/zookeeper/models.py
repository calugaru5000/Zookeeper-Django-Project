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

    def __str__(self):
        return f"{self.name} ({self.get_diet_display()})"

    class Meta:
        verbose_name_plural = "Species"

class Enclosure(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=1)
    diet_type = models.CharField(
        max_length=20,
        choices=Species.DIET_CHOICES,
        help_text="Preferred diet type for this enclosure"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ Add this new field:
    last_cleaned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_diet_type_display()})"

    @property
    def current_occupancy(self):
        return self.animal_set.count()

    @property
    def is_full(self):
        return self.current_occupancy >= self.capacity

    @property
    def needs_cleaning(self):
        if not self.last_cleaned_at:
            return True
        return (timezone.now() - self.last_cleaned_at).total_seconds() > 168 * 3600

class Animal(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    enclosure = models.ForeignKey(Enclosure, on_delete=models.CASCADE)
    last_fed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def needs_feeding(self):
        if not self.last_fed_at:
            return True
        return (timezone.now() - self.last_fed_at).total_seconds() > 24 * 3600

class StaffRole(models.Model):
    """
    Defines staff roles based on enclosure functions.
    Staff members are assigned to specific enclosures with defined roles and permissions.
    """
    ROLE_CHOICES = [
        ('manager', 'Manager'),        # Full control: manage animals, staff, enclosure settings
        ('keeper', 'Keeper'),          # Care duties: feed, monitor health, clean enclosure
        ('monitor', 'Monitor'),        # Read-only: view animals and health status
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_roles')
    enclosure = models.ForeignKey(Enclosure, on_delete=models.CASCADE, related_name='staff_assignments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='monitor')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='staff_assignments_made')

    class Meta:
        unique_together = ('user', 'enclosure')
        verbose_name_plural = "Staff Roles"
        ordering = ['enclosure', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.enclosure.name} ({self.get_role_display()})"

    def can_edit_animals(self):
        """Manager and Keeper can edit animals."""
        return self.role in ['manager', 'keeper']

    def can_manage_enclosure(self):
        """Only Manager can manage enclosure settings."""
        return self.role == 'manager'

    def can_manage_staff(self):
        """Only Manager can manage other staff."""
        return self.role == 'manager'

    def can_clean_enclosure(self):
        """Manager and Keeper can mark enclosure as cleaned."""
        return self.role in ['manager', 'keeper']
