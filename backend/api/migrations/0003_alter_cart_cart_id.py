# Generated by Django 4.2.7 on 2024-11-05 15:42

from django.db import migrations
import shortuuid.django_fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_category_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='cart_id',
            field=shortuuid.django_fields.ShortUUIDField(alphabet='1234567890', length=6, max_length=20, prefix=''),
        ),
    ]