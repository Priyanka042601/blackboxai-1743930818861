from google.cloud import aiplatform
from django.conf import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        aiplatform.init(
            project=settings.VERTEX_AI_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        self.endpoint = aiplatform.Endpoint(
            settings.VERTEX_AI_ENDPOINT_ID
        )

    def detect_anomalies(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in sensor data using Vertex AI"""
        try:
            # Prepare input data for the model
            instance = {
                "latitude": float(sensor_data.get('latitude', 0)),
                "longitude": float(sensor_data.get('longitude', 0)),
                "temperature": float(sensor_data.get('temperature', 0)),
                "humidity": float(sensor_data.get('humidity', 0)),
                "vibration": float(sensor_data.get('vibration', 0))
            }

            # Make prediction
            response = self.endpoint.predict(instances=[instance])
            predictions = response.predictions[0]
            
            return {
                'is_anomaly': bool(predictions.get('is_anomaly', False)),
                'anomaly_score': float(predictions.get('anomaly_score', 0)),
                'confidence': float(predictions.get('confidence', 0))
            }

        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0,
                'confidence': 0
            }

    def should_trigger_alert(self, anomaly_score: float) -> bool:
        """Determine if an alert should be triggered based on anomaly score"""
        return anomaly_score > 0.7  # Threshold can be adjusted