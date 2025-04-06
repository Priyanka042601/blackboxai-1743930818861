from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Shipment, SensorData, Alert
from .serializers import (
    ShipmentSerializer,
    ShipmentCreateSerializer,
    ShipmentUpdateSerializer,
    SensorDataSerializer,
    AlertSerializer
)
from authentication.models import CustomUser
from django.shortcuts import get_object_or_404
from firebase_admin import messaging
from .ml_service import MLService
from blockchain.models import BlockchainTransaction
import json
import logging

logger = logging.getLogger(__name__)

class ShipmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShipmentCreateSerializer
        return ShipmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'MANUFACTURER':
            return Shipment.objects.filter(manufacturer=user)
        return Shipment.objects.all()

    def perform_create(self, serializer):
        serializer.save(manufacturer=self.request.user)

class ShipmentRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Shipment.objects.all()
    lookup_field = 'tracking_id'

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return ShipmentUpdateSerializer
        return ShipmentSerializer

class SensorDataCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SensorDataSerializer
    queryset = SensorData.objects.all()

    def perform_create(self, serializer):
        shipment = get_object_or_404(
            Shipment,
            tracking_id=self.kwargs['tracking_id']
        )
        
        # Run anomaly detection
        ml_service = MLService()
        anomaly_result = ml_service.detect_anomalies(
            serializer.validated_data
        )
        
        # Save sensor data with anomaly results
        sensor_data = serializer.save(
            shipment=shipment,
            is_anomaly=anomaly_result['is_anomaly'],
            anomaly_score=anomaly_result['anomaly_score']
        )
        
        # Record to blockchain
        BlockchainTransaction.record_sensor_data(sensor_data)

        # Check for tampering or anomalies
        if (serializer.validated_data.get('tamper_status', False) or 
            ml_service.should_trigger_alert(anomaly_result['anomaly_score'])):
            
            alert_message = "Tamper detected!" if serializer.validated_data.get('tamper_status', False) \
                else f"Anomaly detected (Score: {anomaly_result['anomaly_score']:.2f})"
            
            self._create_alert(
                shipment,
                alert_message,
                "CRITICAL" if anomaly_result['anomaly_score'] > 0.8 else "HIGH"
            )

    def _create_alert(self, shipment, message, severity):
        try:
            alert = Alert.objects.create(
                shipment=shipment,
                message=message,
                severity=severity
            )
            self._send_firebase_notification(alert)
            BlockchainTransaction.record_alert(alert)
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")

    def _send_firebase_notification(self, alert):
        from .firebase_utils import send_push_notification
        customs_officers = CustomUser.objects.filter(role='CUSTOMS')
        tokens = [o.firebase_token for o in customs_officers if o.firebase_token]
        
        if tokens:
            send_push_notification(
                tokens=tokens,
                title=f"Alert: {alert.severity}",
                body=alert.message,
                data={
                    'alert_id': str(alert.id),
                    'shipment_id': alert.shipment.tracking_id
                }
            )

class AlertListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'CUSTOMS':
            return Alert.objects.filter(resolved=False)
        return Alert.objects.filter(
            shipment__manufacturer=user,
            resolved=False
        )

class AlertResolveView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

    def update(self, request, *args, **kwargs):
        alert = self.get_object()
        alert.resolved = True
        alert.resolved_by = request.user
        alert.save()
        return Response(
            {'status': 'Alert resolved'},
            status=status.HTTP_200_OK
        )