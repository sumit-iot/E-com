# Generated migration for ReturnRequest refund fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_returnrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnrequest',
            name='refund_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='razorpay_refund_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='refund_status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='refunded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

