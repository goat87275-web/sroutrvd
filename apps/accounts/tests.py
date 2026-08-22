from decimal import Decimal
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from apps.marketplace.models import Category, Service
from apps.core.models import TermsAndConditions, TermsAcceptance
from .forms import ProviderDocumentForm, ProviderProfileForm
from .models import ProviderDocument, ProviderDocumentType, User

class ProviderDocumentValidationTests(TestCase):
    def setUp(self):
        self.doc_type=ProviderDocumentType.objects.get(code='IDENTITY')
    def test_rejects_executable_upload(self):
        form=ProviderDocumentForm(data={'document_type':self.doc_type.pk}, files={'file':SimpleUploadedFile('bad.exe', b'MZ', content_type='application/x-msdownload')})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)
    def test_accepts_pdf_upload_and_saves_private_document(self):
        user=User.objects.create_user(username='provider-doc', email='pd@example.com', password='x', role='provider')
        form=ProviderDocumentForm(data={'document_type':self.doc_type.pk}, files={'file':SimpleUploadedFile('id.pdf', b'%PDF-1.4', content_type='application/pdf')})
        self.assertTrue(form.is_valid(), form.errors)
        doc=form.save(commit=False); doc.provider=user.provider_profile; doc.save()
        self.assertTrue(doc.file.name.startswith('provider_documents/'))

    def test_staff_can_open_provider_document_securely(self):
        owner=User.objects.create_user(username='staff-owner', email='staff-owner@example.com', password='x', role='provider')
        staff=User.objects.create_user(username='staff-user', email='staff@example.com', password='x', role='admin', is_staff=True)
        doc=ProviderDocument.objects.create(provider=owner.provider_profile, document_type=self.doc_type, file=SimpleUploadedFile('id.pdf', b'%PDF', content_type='application/pdf'))
        self.client.force_login(staff)
        response=self.client.get(reverse('accounts:provider_document_download', args=[doc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'].split(';')[0], 'attachment')
    def test_provider_cannot_download_another_provider_document(self):
        owner=User.objects.create_user(username='owner', email='owner@example.com', password='x', role='provider')
        other=User.objects.create_user(username='other', email='other@example.com', password='x', role='provider')
        doc=ProviderDocument.objects.create(provider=owner.provider_profile, document_type=self.doc_type, file=SimpleUploadedFile('id.pdf', b'%PDF', content_type='application/pdf'))
        self.client.force_login(other)
        response=self.client.get(reverse('accounts:provider_document_download', args=[doc.pk]))
        self.assertEqual(response.status_code, 302)

class ProviderLocationAndOnboardingTests(TestCase):
    def test_provider_profile_form_saves_location_coordinates(self):
        user=User.objects.create_user(username='map-provider', email='map@example.com', password='x', role='provider')
        form=ProviderProfileForm(data={'bio':'Bio','specialization':'Design','experience_years':3,'hourly_rate':'10.00','address':'Street','city':'Sanaa','district':'Old City','latitude':'15.369400','longitude':'44.191000','service_radius':10,'availability':'Daily','qualifications':'Cert','experience':'Work','is_available':'on'}, instance=user.provider_profile)
        self.assertTrue(form.is_valid(), form.errors)
        profile=form.save()
        self.assertEqual(profile.latitude, Decimal('15.369400'))
        self.assertEqual(profile.longitude, Decimal('44.191000'))
    def test_submit_review_requires_checklist(self):
        user=User.objects.create_user(username='incomplete', email='inc@example.com', password='x', role='provider')
        self.client.force_login(user)
        response=self.client.post(reverse('accounts:provider_submit_review'))
        user.provider_profile.refresh_from_db()
        self.assertNotEqual(user.provider_profile.verification_status, 'pending_review')
        self.assertEqual(response.status_code, 302)

from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import override_settings

class ProviderEditPersistenceViewTests(TestCase):
    def test_provider_edit_saves_user_profile_provider_profile_and_location(self):
        user = User.objects.create_user(username='edit-provider', email='old@example.com', password='x', role='provider')
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:provider_profile_edit'), {
            'user-first_name': 'Ali',
            'user-last_name': 'Provider',
            'user-email': 'ali@example.com',
            'user-phone': '771234567',
            'user-city': 'Sanaa User',
            'provider-business_name': 'Ali Services',
            'provider-display_name': 'Ali Pro',
            'provider-bio': 'Experienced provider bio',
            'provider-phone': '778888888',
            'provider-email': 'business@example.com',
            'provider-specialization': 'Electrical',
            'provider-experience_years': '7',
            'provider-qualifications': 'Certified electrician',
            'provider-experience': 'Residential and commercial work',
            'provider-hourly_rate': '25.50',
            'provider-address': 'Main street',
            'provider-city': 'Sanaa Work',
            'provider-district': 'Old City',
            'provider-latitude': '15.369400',
            'provider-longitude': '44.191000',
            'provider-service_radius': '15',
            'provider-availability': 'Daily',
            'provider-is_available': 'on',
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        profile = user.provider_profile
        profile.refresh_from_db()
        self.assertEqual(user.first_name, 'Ali')
        self.assertEqual(user.email, 'ali@example.com')
        self.assertEqual(profile.business_name, 'Ali Services')
        self.assertEqual(profile.display_name, 'Ali Pro')
        self.assertEqual(profile.specialization, 'Electrical')
        self.assertEqual(profile.city, 'Sanaa Work')
        self.assertEqual(profile.phone, '778888888')
        self.assertEqual(profile.email, 'business@example.com')
        self.assertEqual(profile.district, 'Old City')
        self.assertEqual(profile.latitude, Decimal('15.369400'))
        self.assertEqual(profile.longitude, Decimal('44.191000'))

    def test_provider_profile_form_rejects_invalid_coordinates(self):
        user = User.objects.create_user(username='bad-map', email='bad-map@example.com', password='x', role='provider')
        form = ProviderProfileForm(data={
            'business_name': '', 'display_name': '', 'bio': '', 'phone': '', 'email': '', 'specialization': '',
            'experience_years': '0', 'qualifications': '', 'experience': '', 'hourly_rate': '', 'address': '',
            'city': '', 'district': '', 'latitude': '99.000000', 'longitude': '44.000000',
            'service_radius': '10', 'availability': '',
        }, instance=user.provider_profile)
        self.assertFalse(form.is_valid())
        self.assertIn('latitude', form.errors)

class ProviderDocumentStorageFallbackTests(TestCase):
    def test_secure_download_falls_back_to_legacy_media_file_without_public_url(self):
        with TemporaryDirectory() as media_dir, TemporaryDirectory() as private_dir:
            with override_settings(MEDIA_ROOT=media_dir, PRIVATE_MEDIA_ROOT=private_dir):
                owner = User.objects.create_user(username='legacy-owner', email='legacy-owner@example.com', password='x', role='provider')
                staff = User.objects.create_user(username='legacy-staff', email='legacy-staff@example.com', password='x', role='admin', is_staff=True)
                doc_type = ProviderDocumentType.objects.get(code='IDENTITY')
                legacy_rel = 'provider_documents/provider_%s/legacy.png' % owner.provider_profile.pk
                legacy_path = Path(media_dir) / legacy_rel
                legacy_path.parent.mkdir(parents=True, exist_ok=True)
                legacy_path.write_bytes(b'legacy-bytes')
                doc = ProviderDocument.objects.create(provider=owner.provider_profile, document_type=doc_type)
                doc.file.name = legacy_rel
                doc.save(update_fields=['file'])
                self.client.force_login(staff)
                response = self.client.get(reverse('accounts:provider_document_download', args=[doc.pk]))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), b'legacy-bytes')
