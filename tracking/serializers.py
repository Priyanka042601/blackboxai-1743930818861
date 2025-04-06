from rest_framework import serializers
from .models import Shipment, SensorData, Alert
from authentication.serializers import UserSerializer

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = [
            'id',
            'timestamp',
            'latitude',
            'longitude',
            'temperature',
            'humidity',
            'vibration',
            'tamper_status',
            'is_anomaly',
            'anomaly_score'
        ]
        read_only_fields = ['id', 'timestamp', 'is_anomaly', 'anomaly_score']

class AlertSerializer(serializers.ModelSerializer):
    resolved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id',
            'timestamp',
            'message',
            'severity',
            'resolved',
            'resolved_at',
            'resolved_by'
        ]
        read_only_fields = ['id', 'timestamp']

class ShipmentSerializer(serializers.ModelSerializer):
    manufacturer = UserSerializer(read_only=True)
    latest_sensor_data = SensorDataSerializer(
        source='sensor_readings.first',
        read_only=True
    )
    alerts = AlertSerializer(
        source='alerts.all',
        many=True,
        read_only=True
    )

    class Meta:
        model = Shipment
        fields = [
            'tracking_id',
            'manufacturer',
            'product_name',
            'product_code',
            'quantity',
            'origin',
            'destination',
            'created_at',
            'status',
            'current_location',
            'notes',
            'latest_sensor_data',
            'alerts'
        ]
        read_only_fields = [
            'created_at',
            'status',
            'current_location',
            'latest_sensor_data',
            'alerts'
        ]

class ShipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            'product_name',
            'product_code',
            'quantity',
            'origin',
            'destination',
            'notes'
        ]

class ShipmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            'status',
            'current_location',
            'notes'
        ]