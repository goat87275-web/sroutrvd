from abc import ABC, abstractmethod
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from apps.core.models import TermsAndConditions, calculate_commission
from apps.core.services import notify, audit
from .models import Payment, CommissionRecord, ProviderWallet

class PaymentGateway(ABC):
    name = 'base'
    @abstractmethod
    def create_payment(self, order, amount): raise NotImplementedError
    @abstractmethod
    def verify_payment(self, payment): raise NotImplementedError
    @abstractmethod
    def refund_payment(self, payment): raise NotImplementedError

class ManualPaymentGateway(PaymentGateway):
    name = 'manual_wallet'
    def create_payment(self, order, amount):
        return {'transaction_id': f'MANUAL-{order.order_number}-{timezone.now().strftime("%Y%m%d%H%M%S")}', 'status': Payment.STATUS_PENDING}
    def verify_payment(self, payment): return payment.status == Payment.STATUS_PAID
    def refund_payment(self, payment): return {'refunded': True}

class TestPaymentGateway(PaymentGateway):
    name = 'test'
    def create_payment(self, order, amount):
        return {'transaction_id': f'TEST-{order.order_number}-{timezone.now().strftime("%Y%m%d%H%M%S")}', 'status': Payment.STATUS_PROCESSING}
    def verify_payment(self, payment): return True
    def refund_payment(self, payment): return {'refunded': True}

def get_gateway(name='manual_wallet'):
    if name == 'test' and settings.DEBUG: return TestPaymentGateway()
    return ManualPaymentGateway()

def active_terms():
    return TermsAndConditions.objects.filter(is_active=True).first()

def current_commission_rate():
    terms = active_terms()
    return terms.commission_rate if terms else 0

@transaction.atomic
def create_payment(order, provider_wallet=None, method='manual_wallet', gateway_name='manual_wallet'):
    existing = Payment.objects.filter(order=order, status__in=[Payment.STATUS_PENDING, Payment.STATUS_PROCESSING, Payment.STATUS_UNDER_REVIEW, Payment.STATUS_REJECTED]).order_by('-created_at').first()
    if existing and provider_wallet is None: return existing
    if provider_wallet is None: raise ValueError('يجب اختيار محفظة مقدم الخدمة.')
    if provider_wallet.provider.user_id != order.provider_id or not provider_wallet.is_active or not provider_wallet.wallet.is_active:
        raise ValueError('المحفظة المحددة غير صالحة لهذا الطلب.')
    gateway=get_gateway(gateway_name); data=gateway.create_payment(order, order.agreed_price)
    rate=current_commission_rate(); amounts=calculate_commission(order.agreed_price, rate)
    payment=Payment.objects.create(order=order, provider_wallet=provider_wallet, provider_wallet_account_snapshot=provider_wallet.account_number, amount=order.agreed_price, currency=getattr(order,'currency','YER'), payment_method=method, gateway=gateway.name, transaction_id=data['transaction_id'], status=data.get('status', Payment.STATUS_PENDING), commission_rate=amounts['commission_rate'], commission_amount=amounts['commission_amount'], provider_net_amount=amounts['provider_net_amount'])
    order.commission_rate=amounts['commission_rate']; order.commission_amount=amounts['commission_amount']; order.provider_net_amount=amounts['provider_net_amount']; order.save(update_fields=['commission_rate','commission_amount','provider_net_amount'])
    return payment

@transaction.atomic
def submit_payment_proof(payment, proof_file, actor):
    if actor != payment.order.customer: raise PermissionError('Only customer can upload payment proof.')
    payment.proof_file=proof_file; payment.proof_uploaded_at=timezone.now(); payment.status=Payment.STATUS_UNDER_REVIEW; payment.save(update_fields=['proof_file','proof_uploaded_at','status','updated_at'])
    payment.order.payment_status='processing'; payment.order.save(update_fields=['payment_status'])
    notify(payment.order.provider,'payment_proof_uploaded','تم رفع سند حوالة',f'تم رفع سند حوالة للطلب {payment.order.order_number}، يرجى مراجعة الدفع.')
    audit(actor,'payment_proof_uploaded',payment, order=payment.order.order_number)
    return payment

@transaction.atomic
def mark_payment_paid(payment, actor=None):
    payment.status=Payment.STATUS_PAID; payment.paid_at=timezone.now(); payment.reviewed_by=actor; payment.reviewed_at=timezone.now(); payment.save(update_fields=['status','paid_at','reviewed_by','reviewed_at','updated_at'])
    order=payment.order; order.payment_status='paid'
    if order.status == order.STATUS_PAYMENT_PENDING: order.transition_to(order.STATUS_PAID, actor=actor)
    order.save()
    amounts={'gross_amount':payment.amount,'commission_rate':payment.commission_rate or current_commission_rate(),'commission_amount':payment.commission_amount or 0,'provider_net_amount':payment.provider_net_amount or payment.amount}
    if payment.commission_amount is None:
        amounts=calculate_commission(payment.amount, amounts['commission_rate'])
        payment.commission_rate=amounts['commission_rate']; payment.commission_amount=amounts['commission_amount']; payment.provider_net_amount=amounts['provider_net_amount']; payment.save(update_fields=['commission_rate','commission_amount','provider_net_amount','updated_at'])
    CommissionRecord.objects.update_or_create(order=order, defaults={**amounts,'payment':payment,'currency':payment.currency})
    order.commission_rate=amounts['commission_rate']; order.commission_amount=amounts['commission_amount']; order.provider_net_amount=amounts['provider_net_amount']; order.save(update_fields=['commission_rate','commission_amount','provider_net_amount'])
    notify(order.customer,'payment_successful','تم تأكيد الدفع',f'تم تأكيد الدفع للطلب {order.order_number}.')
    audit(actor,'payment_paid',payment, order=order.order_number)
    return payment

@transaction.atomic
def mark_payment_failed(payment, actor=None, reason=''):
    payment.status=Payment.STATUS_REJECTED; payment.reviewed_by=actor; payment.reviewed_at=timezone.now(); payment.review_note=reason; payment.save(update_fields=['status','reviewed_by','reviewed_at','review_note','updated_at'])
    order=payment.order; order.payment_status='failed'; order.save(update_fields=['payment_status'])
    notify(order.customer,'payment_failed','تم رفض سند الحوالة',f'تم رفض سند حوالة الطلب {order.order_number}. السبب: {reason}')
    audit(actor,'payment_rejected',payment, reason=reason, order=order.order_number)
    return payment
