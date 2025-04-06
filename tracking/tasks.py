from celery import shared_task
import logging
from tracking.models import SensorData
from blockchain.models import BlockchainTransaction
from tracking.iot_core_service import IoTCoreService
from tracking.ml_service import MLService

logger = logging.getLogger(__name__)

@shared_task(name="process_iot_messages")
def process_iot_messages():
    """Process incoming IoT Core messages"""
    try:
        service = IoTCoreService()
        service.start_ingestion()
    except Exception as e:
        logger.error(f"IoT message processing failed: {e}")
        raise

@shared_task(name="sync_blockchain")
def sync_blockchain():
    """Sync unrecorded transactions to blockchain"""
    try:
        unrecorded = SensorData.objects.filter(blockchain_recorded=False)
        count = 0
        for data in unrecorded:
            BlockchainTransaction.record_sensor_data(data)
            data.blockchain_recorded = True
            data.save()
            count += 1
        logger.info(f"Synced {count} records to blockchain")
    except Exception as e:
        logger.error(f"Blockchain sync failed: {e}")
        raise

@shared_task(name="detect_anomalies")
def detect_anomalies(sensor_data_id):
    """Run anomaly detection on sensor data"""
    try:
        data = SensorData.objects.get(id=sensor_data_id)
        ml = MLService()
        result = ml.detect_anomalies({
            'latitude': data.latitude,
            'longitude': data.longitude,
            'temperature': data.temperature, 
            'humidity': data.humidity,
            'vibration': data.vibration
        })
        
        data.is_anomaly = result['is_anomaly']
        data.anomaly_score = result['anomaly_score']
        data.save()
        
        if result['is_anomaly']:
            from tracking.views import SensorDataCreateView
            view = SensorDataCreateView()
            view._create_alert(
                data.shipment,
                f"Anomaly detected (score: {result['anomaly_score']:.2f})",
                "CRITICAL" if result['anomaly_score'] > 0.8 else "HIGH"
            )
            
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise