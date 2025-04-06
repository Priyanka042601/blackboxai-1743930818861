from django.db import models
from tracking.models import Shipment, SensorData, Alert
from web3 import Web3
import json
from django.conf import settings

class BlockchainTransaction(models.Model):
    EVENT_TYPES = [
        ('SHIPMENT_CREATED', 'Shipment Created'),
        ('SENSOR_DATA', 'Sensor Data'),
        ('ALERT', 'Alert'),
        ('STATUS_CHANGE', 'Status Change'),
    ]

    transaction_hash = models.CharField(max_length=66, unique=True)
    block_number = models.PositiveIntegerField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_data = models.JSONField()
    timestamp = models.DateTimeField()
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-block_number']

    def __str__(self):
        return f"{self.event_type} - {self.transaction_hash}"

    @classmethod
    def record_shipment_creation(cls, shipment):
        w3 = Web3(Web3.HTTPProvider(cls._get_node_url()))
        contract = cls._get_contract(w3)
        
        tx_hash = contract.functions.recordShipment(
            str(shipment.tracking_id),
            shipment.manufacturer.username,
            shipment.product_name,
            shipment.origin,
            shipment.destination
        ).transact({
            'from': cls._get_admin_address(),
            'gas': 1000000
        })
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return cls._create_from_receipt(receipt, 'SHIPMENT_CREATED', {
            'tracking_id': str(shipment.tracking_id),
            'manufacturer': shipment.manufacturer.username,
            'product_name': shipment.product_name,
            'origin': shipment.origin,
            'destination': shipment.destination
        })

    @classmethod
    def record_sensor_data(cls, sensor_data):
        w3 = Web3(Web3.HTTPProvider(cls._get_node_url()))
        contract = cls._get_contract(w3)
        
        tx_hash = contract.functions.recordSensorData(
            str(sensor_data.shipment.tracking_id),
            float(sensor_data.latitude),
            float(sensor_data.longitude),
            float(sensor_data.temperature),
            float(sensor_data.humidity),
            float(sensor_data.vibration),
            bool(sensor_data.tamper_status),
            bool(sensor_data.is_anomaly),
            float(sensor_data.anomaly_score) if sensor_data.anomaly_score else 0.0
        ).transact({
            'from': cls._get_admin_address(),
            'gas': 1000000
        })
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return cls._create_from_receipt(receipt, 'SENSOR_DATA', {
            'tracking_id': str(sensor_data.shipment.tracking_id),
            'latitude': float(sensor_data.latitude),
            'longitude': float(sensor_data.longitude),
            'temperature': float(sensor_data.temperature),
            'humidity': float(sensor_data.humidity),
            'vibration': float(sensor_data.vibration),
            'tamper_status': bool(sensor_data.tamper_status),
            'is_anomaly': bool(sensor_data.is_anomaly),
            'anomaly_score': float(sensor_data.anomaly_score) if sensor_data.anomaly_score else 0.0
        })

    @classmethod
    def _get_node_url(cls):
        return settings.BLOCKCHAIN_NODE_URL

    @classmethod
    def _get_contract(cls, w3):
        with open('blockchain/contracts/ShipmentTracking.json') as f:
            contract_abi = json.load(f)['abi']
        return w3.eth.contract(
            address=settings.BLOCKCHAIN_CONTRACT_ADDRESS,
            abi=contract_abi
        )

    @classmethod
    def _get_admin_address(cls):
        return settings.BLOCKCHAIN_ADMIN_ADDRESS

    @classmethod
    def _create_from_receipt(cls, receipt, event_type, event_data):
        block = Web3(Web3.HTTPProvider(cls._get_node_url())).eth.get_block(receipt.blockNumber)
        return cls.objects.create(
            transaction_hash=receipt.transactionHash.hex(),
            block_number=receipt.blockNumber,
            event_type=event_type,
            event_data=event_data,
            timestamp=block.timestamp
        )