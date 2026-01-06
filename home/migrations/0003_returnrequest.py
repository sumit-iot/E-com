# Generated migration for ReturnRequest model

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_order_razorpay_order_id_order_razorpay_payment_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reason', models.CharField(choices=[('defective', 'Defective Product'), ('wrong_item', 'Wrong Item Received'), ('damaged', 'Damaged During Shipping'), ('not_as_described', 'Not as Described'), ('size_issue', 'Size Issue'), ('color_issue', 'Color Issue'), ('other', 'Other')], max_length=50)),
                ('reason_description', models.TextField(blank=True, null=True)),
                ('quantity', models.IntegerField(default=1)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('processing', 'Processing'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('admin_notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to='home.order')),
                ('order_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to='home.orderitem')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_returns', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Return Request',
                'verbose_name_plural': 'Return Requests',
                'db_table': 'return_request',
                'ordering': ['-created_at'],
            },
        ),
    ]

