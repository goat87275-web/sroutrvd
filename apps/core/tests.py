from decimal import Decimal
from django.test import TestCase
from apps.core.models import calculate_commission
class CommissionCalculationTests(TestCase):
    def test_calculate_commission_uses_decimal_snapshot_amounts(self):
        result=calculate_commission(Decimal('100.00'), Decimal('10.00'))
        self.assertEqual(result['commission_amount'], Decimal('10.00'))
        self.assertEqual(result['provider_net_amount'], Decimal('90.00'))
from django.conf import settings

class MapsSettingsTests(TestCase):
    def test_maps_api_key_setting_exists(self):
        self.assertTrue(hasattr(settings, 'MAPS_API_KEY'))
