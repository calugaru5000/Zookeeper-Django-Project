from django.db import migrations

def create_enclosures(apps, schema_editor):
    Animal = apps.get_model('zookeeper', 'Animal')
    Enclosure = apps.get_model('zookeeper', 'Enclosure')
    Species = apps.get_model('zookeeper', 'Species')

    # Get all unique enclosure names from existing animals
    existing_enclosures = set(Animal.objects.values_list('enclosure', flat=True))
    
    # Create an Enclosure object for each unique enclosure name
    for enclosure_name in existing_enclosures:
        # Try to guess the diet type from the animals in this enclosure
        animals_in_enclosure = Animal.objects.filter(enclosure=enclosure_name).select_related('species')
        diet_types = set(animal.species.diet for animal in animals_in_enclosure)
        
        # Use the most common diet type, or 'omnivore' if mixed
        diet_type = list(diet_types)[0] if len(diet_types) == 1 else 'omnivore'
        
        # Create the enclosure
        Enclosure.objects.create(
            name=enclosure_name,
            diet_type=diet_type,
            capacity=max(3, animals_in_enclosure.count()),  # Set capacity to at least 3 or current count
            description=f"Auto-created enclosure for {enclosure_name}"
        )

def reverse_migration(apps, schema_editor):
    Enclosure = apps.get_model('zookeeper', 'Enclosure')
    Enclosure.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('zookeeper', '0004_alter_animal_enclosure'),
    ]

    operations = [
        migrations.RunPython(create_enclosures, reverse_migration),
    ]
