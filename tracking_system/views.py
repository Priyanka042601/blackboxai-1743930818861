from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tracking.models import Shipment, Alert
from authentication.models import CustomUser

@login_required
def dashboard_view(request):
    # Get counts for dashboard stats
    active_shipments = Shipment.objects.exclude(
        status__in=['DELIVERED', 'CANCELLED']
    ).count()
    completed_shipments = Shipment.objects.filter(
        status='DELIVERED'
    ).count()
    active_alerts = Alert.objects.filter(
        resolved=False
    ).count()
    tamper_events = Alert.objects.filter(
        message__icontains='tamper',
        resolved=False
    ).count()

    # Get recent shipments
    recent_shipments = Shipment.objects.order_by('-created_at')[:5]

    context = {
        'active_shipments': active_shipments,
        'completed_shipments': completed_shipments,
        'active_alerts': active_alerts,
        'tamper_events': tamper_events,
        'recent_shipments': recent_shipments,
        'user': request.user
    }
    return render(request, 'dashboard.html', context)