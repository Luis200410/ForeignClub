# Generated manually to sync flashcard meaning/title columns
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_moduleafterburneractivity_goal_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_modulegameflashcard ADD COLUMN IF NOT EXISTS meaning text",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE core_modulegameflashcard DROP COLUMN IF EXISTS image_url",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE core_modulegameflashcard DROP COLUMN IF EXISTS audio_url",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="ALTER TABLE core_moduleafterburnerrealworldstep ADD COLUMN IF NOT EXISTS title varchar(160)",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
