# This migration was duplicated during an attempted change to Enclosure/Animal.
# Convert it into a no-op that depends on the single canonical create_enclosures (0005).
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("zookeeper", "0005_create_enclosures"),
    ]

    operations = [
    ]
