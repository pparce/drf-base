from django.db import migrations, models
import src.apps.user.models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to=src.apps.user.models.avatar_upload_path),
        ),
        migrations.AlterField(
            model_name="user",
            name="restore_code",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(verbose_name="First Name", max_length=255, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(verbose_name="Last Name", max_length=255, blank=True, null=True),
        ),
    ]
