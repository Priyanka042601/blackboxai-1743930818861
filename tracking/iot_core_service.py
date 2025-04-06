import json
from google.cloud import pubsub_v1
from google.api_core import retry
from django.conf import settings
from tracking.models import SensorData
from blockchain.models import BlockchainTransaction
import logging

logger = logging.getLogger(__name__)

class IoTCoreService:
    def __init__(self):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            settings.GCP_IOT_CORE_PROJECT,
            settings.GCP_PUBSUB_SUBSCRIPTION
        )

    def start_ingestion(self):
        """Start listening for IoT Core messages"""
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self._process_message,
            retry=retry.Retry(deadline=300)
        )
        logger.info(f"Listening for messages on {self.subscription_path}...")
        return streaming_pull_future

    def _process_message(self, message):
        """Process incoming IoT Core message"""
        try:
            data = json.loads(message.data.decode('utf-8'))
            device_id = message.attributes['deviceId']
            
            # Validate and save sensor data
            sensor_data = self._save_sensor_data(device_id, data)
            
            # Record to blockchain
            BlockchainTransaction.record_sensor_data(sensor_data)
            
            message.ack()
            logger.info(f"Processed message from {device_id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            message.nack()

    def _save_sensor_data(self, device_id, data):
        """Save sensor data to database"""
        try:
            # Get associated shipment
            shipment = self._get_shipment_for_device(device_id)
            
            # Create sensor data record
            sensor_data = SensorData.objects.create(
                shipment=shipment,
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                temperature=data.get('temperature'),
                humidity=data.get('humidity'),
                vibration=data.get('vibration'),
                tamper_status=data.get('tamper_status', False)
            )
            return sensor_data
            
        except Exception as e:
            logger.error(f"Error saving sensor data: {str(e)}")
            raise

    def _get_shipment_for_device(self, device_id):
        """Get shipment associated with IoT device"""
        # Implementation depends on how devices are mapped to shipments
        # This is a placeholder - actual implementation may vary
        from tracking.models import Shipment
        return Shipment.objects.get(tracking_id=device_id.split('_')[0])