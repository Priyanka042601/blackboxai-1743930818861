from rest_framework import serializers
from .models import BlockchainTransaction

class BlockchainTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockchainTransaction
        fields = [
            'transaction_hash',
            'block_number',
            'event_type',
            'event_data',
            'timestamp',
            'processed'
        ]
        read_only_fields = fields

class EventFilterSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(
        choices=BlockchainTransaction.EVENT_TYPES,
        required=False
    )
    from_block = serializers.IntegerField(min_value=0, required=False)
    to_block = serializers.IntegerField(min_value=0, required=False)
    tracking_id = serializers.CharField(required=False)

    def validate(self, data):
        if 'from_block' in data and 'to_block' in data:
            if data['from_block'] > data['to_block']:
                raise serializers.ValidationError(
                    "from_block cannot be greater than to_block"
                )
        return data