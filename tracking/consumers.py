import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from tracking.models import Shipment, SensorData, Alert

class ShipmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_initial_data()

    async def disconnect(self, close_code):
        pass

    @sync_to_async
    def get_initial_data(self):
        return {
            'shipments': list(Shipment.objects.values(
                'tracking_id', 'product_name', 'status', 
                'current_location', 'updated_at'
            )),
            'alerts': list(Alert.objects.filter(resolved=False).values(
                'id', 'message', 'severity', 'created_at',
                'shipment__tracking_id'
            ))
        }

    async def send_initial_data(self):
        initial_data = await self.get_initial_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'payload': initial_data
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': data.get('timestamp')
            }))