from django.db import models
from authentication.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('HELD', 'Held'),
        ('TAMPERED', 'Tampered'),
    ]

    tracking_id = models.CharField(max_length=64, unique=True)
    manufacturer = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='manufactured_shipments'
    )
    product_name = models.CharField(max_length=100)
    product_code = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='CREATED'
    )
    current_location = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product_name} ({self.tracking_id})"

class SensorData(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='sensor_readings'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    temperature = models.FloatField(
        validators=[MinValueValidator(-50), MaxValueValidator(100)]
    )
    humidity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    vibration = models.FloatField()
    tamper_status = models.BooleanField(default=False)
    is_anomaly = models.BooleanField(default=False)
    anomaly_score = models.FloatField(null=True, blank=True)
    blockchain_recorded = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Sensor data for {self.shipment.tracking_id} at {self.timestamp}"

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    severity = models.CharField(max_length=8, choices=SEVERITY_CHOICES)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Alert for {self.shipment.tracking_id}: {self.message[:50]}..."