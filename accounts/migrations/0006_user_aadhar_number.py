# Generated manually on 2026-02-27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_user_address_user_date_of_birth_user_upi_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="aadhar_number",
            field=models.CharField(
                blank=True,
                help_text="Student's 12-digit Aadhaar number",
                max_length=12,
                null=True,
            ),
        ),
    ]
