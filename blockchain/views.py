from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import BlockchainTransaction
from .serializers import BlockchainTransactionSerializer
from web3 import Web3
import json
from django.conf import settings

class TransactionVerifyView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlockchainTransactionSerializer
    lookup_field = 'transaction_hash'
    queryset = BlockchainTransaction.objects.all()

class EventListenerView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_NODE_URL))
        
        # Get contract instance
        with open('blockchain/contracts/ShipmentTracking.json') as f:
            contract_abi = json.load(f)['abi']
        contract = w3.eth.contract(
            address=settings.BLOCKCHAIN_CONTRACT_ADDRESS,
            abi=contract_abi
        )

        # Get latest processed block number
        last_block = BlockchainTransaction.objects.order_by('-block_number').first()
        from_block = last_block.block_number if last_block else 0

        # Get new events
        events = contract.events.all_events().get_logs(fromBlock=from_block + 1)

        # Process events
        for event in events:
            self._process_event(event)

        return Response(
            {'status': f'Processed {len(events)} new events'},
            status=status.HTTP_200_OK
        )

    def _process_event(self, event):
        event_type = event.event
        event_data = dict(event.args)

        # Skip if transaction already exists
        if BlockchainTransaction.objects.filter(
            transaction_hash=event.transactionHash.hex()
        ).exists():
            return

        # Create transaction record
        block = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_NODE_URL)).eth.get_block(event.blockNumber)
        BlockchainTransaction.objects.create(
            transaction_hash=event.transactionHash.hex(),
            block_number=event.blockNumber,
            event_type=event_type.upper(),
            event_data=event_data,
            timestamp=block.timestamp,
            processed=True
        )