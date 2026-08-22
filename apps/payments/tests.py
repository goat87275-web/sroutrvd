from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.accounts.models import User
from apps.core.models import TermsAndConditions, TermsAcceptance, Notification
from apps.marketplace.models import Category, Service
from apps.orders.models import Order
from .models import Payment, CommissionRecord, Wallet, ProviderWallet

class PaymentWorkflowTests(TestCase):
    def setUp(self):
        self.customer=User.objects.create_user(username='cust', email='cust@example.com', password='x', role='customer')
        self.provider=User.objects.create_user(username='prov', email='prov@example.com', password='x', role='provider')
        self.terms=TermsAndConditions.objects.create(version='v1', content='terms', commission_rate=10, is_active=True)
        self.wallet=Wallet.objects.create(name='جيب', code='jaib-test', color='#dc3545', is_active=True)
        self.provider_wallet=ProviderWallet.objects.create(provider=self.provider.provider_profile, wallet=self.wallet, account_number='777123456', is_active=True)
        cat=Category.objects.create(name='Dev')
        self.service=Service.objects.create(provider=self.provider, category=cat, title='Web', description='Build', price=100, delivery_time=3, status='active')
        self.order=Order.objects.create(customer=self.customer, provider=self.provider, service=self.service, title='Web', description='Need', agreed_price=100, delivery_days=3, status=Order.STATUS_PAYMENT_PENDING)
    def test_create_payment_keeps_order_unpaid_and_snapshots_wallet_commission(self):
        self.client.force_login(self.customer)
        response=self.client.post(reverse('payments:payment_create', args=[self.order.order_number]), {'provider_wallet': self.provider_wallet.pk})
        self.assertEqual(response.status_code, 302)
        payment=Payment.objects.get(order=self.order)
        self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.provider_wallet_account_snapshot, '777123456')
        self.assertEqual(payment.commission_rate, Decimal('10.00'))
        self.assertEqual(payment.commission_amount, Decimal('10.00'))
        self.assertEqual(payment.provider_net_amount, Decimal('90.00'))
        self.assertEqual(self.order.payment_status, 'pending')
        self.assertEqual(self.order.status, Order.STATUS_PAYMENT_PENDING)
    def test_commission_snapshot_does_not_change_when_admin_changes_terms(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('payments:payment_create', args=[self.order.order_number]), {'provider_wallet': self.provider_wallet.pk})
        payment=Payment.objects.get(order=self.order)
        self.terms.commission_rate=15; self.terms.save()
        payment.refresh_from_db()
        self.assertEqual(payment.commission_rate, Decimal('10.00'))
    def test_customer_uploads_proof_provider_approves_payment(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('payments:payment_create', args=[self.order.order_number]), {'provider_wallet': self.provider_wallet.pk})
        payment=Payment.objects.get(order=self.order)
        proof=SimpleUploadedFile('proof.png', b'proof', content_type='image/png')
        self.client.post(reverse('payments:payment_submit_proof', args=[payment.pk]), {'proof_file': proof})
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_UNDER_REVIEW)
        self.assertTrue(Notification.objects.filter(recipient=self.provider, event_type='payment_proof_uploaded').exists())
        self.client.force_login(self.provider)
        self.client.post(reverse('payments:payment_approve', args=[payment.pk]))
        payment.refresh_from_db(); self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertTrue(CommissionRecord.objects.filter(order=self.order).exists())
    def test_provider_rejects_payment_with_reason(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('payments:payment_create', args=[self.order.order_number]), {'provider_wallet': self.provider_wallet.pk})
        payment=Payment.objects.get(order=self.order)
        self.client.post(reverse('payments:payment_submit_proof', args=[payment.pk]), {'proof_file': SimpleUploadedFile('proof.png', b'proof', content_type='image/png')})
        self.client.force_login(self.provider)
        self.client.post(reverse('payments:payment_reject', args=[payment.pk]), {'reason':'غير واضح'})
        payment.refresh_from_db(); self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_REJECTED)
        self.assertEqual(self.order.payment_status, 'failed')
        self.assertEqual(payment.review_note, 'غير واضح')
    def test_provider_cannot_start_order_before_paid(self):
        self.client.force_login(self.provider)
        response=self.client.get(reverse('orders:order_start', args=[self.order.order_number]))
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertNotEqual(self.order.status, Order.STATUS_IN_PROGRESS)
    @override_settings(DEBUG=True)
    def test_debug_success_updates_payment_order_and_commission(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('payments:payment_create', args=[self.order.order_number]), {'provider_wallet': self.provider_wallet.pk})
        payment=Payment.objects.get(order=self.order)
        response=self.client.post(reverse('payments:payment_test_success', args=[payment.pk]))
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db(); self.order.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(self.order.status, Order.STATUS_PAID)
        self.assertEqual(self.order.payment_status, 'paid')

class ProviderCommissionWalletTests(TestCase):
    def test_provider_must_accept_commission_before_submit_review(self):
        provider=User.objects.create_user(username='commission-provider', email='cp@example.com', password='x', role='provider')
        TermsAndConditions.objects.create(version='v1', content='terms', commission_rate=12, is_active=True)
        self.client.force_login(provider)
        response=self.client.post(reverse('accounts:provider_submit_review'))
        provider.provider_profile.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TermsAcceptance.objects.filter(user=provider).exists())
        self.assertNotEqual(provider.provider_profile.verification_status, 'pending_review')
        self.client.post(reverse('accounts:accept_commission_policy'))
        acceptance=TermsAcceptance.objects.get(user=provider)
        self.assertEqual(acceptance.commission_rate, Decimal('12.00'))
    def test_provider_can_save_multiple_wallet_accounts(self):
        provider=User.objects.create_user(username='wallet-provider', email='wp@example.com', password='x', role='provider')
        TermsAndConditions.objects.create(version='v1', content='terms', commission_rate=10, is_active=True)
        w1=Wallet.objects.create(name='جيب', code='jaib-local', color='#dc3545')
        w2=Wallet.objects.create(name='جوالي', code='jawali-local', color='#ffc107')
        self.client.force_login(provider)
        response=self.client.post(reverse('accounts:provider_profile_edit'), {
            'user-first_name':'','user-last_name':'','user-email':'wp@example.com','user-phone':'','user-city':'',
            'provider-business_name':'','provider-display_name':'','provider-bio':'','provider-phone':'','provider-email':'','provider-specialization':'','provider-experience_years':'0','provider-qualifications':'','provider-experience':'','provider-hourly_rate':'','provider-address':'','provider-city':'','provider-district':'','provider-latitude':'','provider-longitude':'','provider-service_radius':'10','provider-availability':'','wallets':[str(w1.pk), str(w2.pk)], f'wallet_account_{w1.pk}':'777111111', f'wallet_account_{w2.pk}':'733222222'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProviderWallet.objects.filter(provider=provider.provider_profile, is_active=True).count(), 2)
