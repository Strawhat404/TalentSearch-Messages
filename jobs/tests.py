from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Job
from .serializers import JobSerializer
from datetime import date, datetime
import pytz
from django.contrib.auth import get_user_model
User = get_user_model()
class JobModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.job = Job.objects.create(
            user_id=self.user,
            talents='Talent Description',
            project_type='Film',
            organization_type='Company',
            first_name='Daniel',
            last_name='Yirga',
            company_name='Acme Inc.',
            company_website='https://example.com',
            job_title='Marketing Director',
            country='United States',
            postal_code='90210',
            project_title='Selam Movie Project',
            project_start_date=date(2025, 11, 1),
            project_end_date=date(2026, 5, 31),
            compensation_type='Fixed',
            compensation_amount='Birr50,000',
            project_details='Full production of a feature film'
        )

    def test_model_str(self):
        self.assertEqual(str(self.job), 'Marketing Director at Acme Inc.')

    def test_model_fields(self):
        self.assertEqual(self.job.talents, 'Talent Description')
        self.assertEqual(self.job.project_type, 'Film')
        self.assertEqual(self.job.organization_type, 'Company')
        self.assertEqual(self.job.first_name, 'Daniel')
        self.assertEqual(self.job.last_name, 'Yirga')
        self.assertEqual(self.job.company_name, 'Acme Inc.')
        self.assertEqual(self.job.company_website, 'https://example.com')
        self.assertEqual(self.job.job_title, 'Marketing Director')
        self.assertEqual(self.job.country, 'United States')
        self.assertEqual(self.job.postal_code, '90210')
        self.assertEqual(self.job.project_title, 'Selam Movie Project')
        self.assertEqual(self.job.project_start_date, date(2025, 11, 1))
        self.assertEqual(self.job.project_end_date, date(2026, 5, 31))
        self.assertEqual(self.job.compensation_type, 'Fixed')
        self.assertEqual(self.job.compensation_amount, 'Birr50,000')
        self.assertEqual(self.job.project_details, 'Full production of a feature film')
        self.assertTrue(isinstance(self.job.created_at, datetime))

class JobSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.job = Job.objects.create(
            user_id=self.user,
            talents='Talent Description',
            project_type='Film',
            organization_type='Company',
            first_name='Daniel',
            last_name='Yirga',
            company_name='Acme Inc.',
            company_website='https://example.com',
            job_title='Marketing Director',
            country='United States'
        )

    def test_serializer_missing_required_fields(self):
        data = {
            'project_type': 'Film',
            'organization_type': 'Company'
            # Missing required fields: talents, first_name, last_name, company_name, job_title, country
        }
        serializer = JobSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('talents', serializer.errors)
        self.assertIn('first_name', serializer.errors)
        self.assertIn('last_name', serializer.errors)
        self.assertIn('company_name', serializer.errors)
        self.assertIn('job_title', serializer.errors)
        self.assertIn('country', serializer.errors)
        self.assertEqual(str(serializer.errors['talents'][0]), 'This field is required.')


        self.assertEqual(str(serializer.errors['first_name'][0]), 'This field is required.')
        self.assertEqual(str(serializer.errors['last_name'][0]), 'This field is required.')
        self.assertEqual(str(serializer.errors['company_name'][0]), 'This field is required.'),
        self.assertEqual(str(serializer.errors['job_title'][0]), 'This field is required.')
        self.assertEqual(str(serializer.errors['country'][0]), 'This field is required.')

    def test_serializer_blank_required_fields(self):
        data = {
            'talents': '',
            'project_type': '',
            'organization_type': '',
            'first_name': '',
            'last_name': '',
            'company_name': '',
            'job_title': '',
            'country': ''
        }
        serializer = JobSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        for field in ['talents', 'project_type', 'organization_type', 'first_name', 'last_name', 'company_name', 'job_title', 'country']:
            self.assertIn(field, serializer.errors)
            self.assertEqual(str(serializer.errors[field][0]), 'This field may not be blank.')


    def test_serializer_valid_data(self):
        data = {
            'talents': 'Talent Description',
            'project_type': 'Film',
            'organization_type': 'Company',
            'first_name': 'Daniel',
            'last_name': 'Yirga',
            'company_name': 'Acme Inc.',
            'company_website': 'https://example.com',
            'job_title': 'Marketing Director',
            'country': 'United States',
            'postal_code': '90210',
            'project_title': 'Selam Movie Project',
            'project_start_date': '2025-11-01',
            'project_end_date': '2026-05-31',
            'compensation_type': 'Fixed',
            'compensation_amount': 'Birr50,000',
            'project_details': 'Full production of a feature film'
        }
        serializer = JobSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        job = serializer.save(user_id=self.user)
        self.assertEqual(job.talents, 'Talent Description')
        self.assertEqual(job.project_title, 'Selam Movie Project')
        self.assertEqual(job.project_start_date, date(2025, 11, 1))
        self.assertEqual(job.project_end_date, date(2026, 5, 31))
        self.assertEqual(job.compensation_type, 'Fixed')
        self.assertEqual(job.compensation_amount, 'Birr50,000')
        self.assertEqual(job.project_details, 'Full production of a feature film')

    def test_serializer_partial_update(self):
        data = {
            'talents': 'Updated Talents',
            'project_title': 'Updated Project',
            'compensation_type': 'Hourly'
        }
        serializer = JobSerializer(instance=self.job, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_job = serializer.save()
        self.assertEqual(updated_job.talents, 'Updated Talents')
        self.assertEqual(updated_job.project_title, 'Updated Project')
        self.assertEqual(updated_job.compensation_type, 'Hourly')
        # Ensure other fields remain unchanged
        self.assertEqual(updated_job.first_name, 'Daniel')
        self.assertEqual(updated_job.country, 'United States')

    def test_serializer_partial_update_blank_required_field(self):
        data = {
            'talents': '',
            'project_title': 'Updated Project'
        }
        serializer = JobSerializer(instance=self.job, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('talents', serializer.errors)
        self.assertEqual(str(serializer.errors['talents'][0]), 'This field may not be blank.')


class JobViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.job = Job.objects.create(
            user_id=self.user,
            talents='Talent Description',
            project_type='Film',
            organization_type='Company',
            first_name='Daniel',
            last_name='Yirga',
            company_name='Acme Inc.',
            company_website='https://example.com',
            job_title='Marketing Director',
            country='United States',
            postal_code='90210',
            project_title='Selam Movie Project',
            project_start_date=date(2025, 11, 1),
            project_end_date=date(2026, 5, 31),
            compensation_type='Fixed',
            compensation_amount='Birr50,000',
            project_details='Full production of a feature film'
        )

    def test_get_jobs(self):
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        job_data = response.data[0]
        self.assertEqual(job_data['talents'], 'Talent Description')
        self.assertEqual(job_data['project_type'], 'Film')
        self.assertEqual(job_data['organization_type'], 'Company')
        self.assertEqual(job_data['first_name'], 'Daniel')
        self.assertEqual(job_data['last_name'], 'Yirga')
        self.assertEqual(job_data['company_name'], 'Acme Inc.')
        self.assertEqual(job_data['company_website'], 'https://example.com')
        self.assertEqual(job_data['job_title'], 'Marketing Director')
        self.assertEqual(job_data['country'], 'United States')
        self.assertEqual(job_data['postal_code'], '90210')
        self.assertEqual(job_data['project_title'], 'Selam Movie Project')
        self.assertEqual(job_data['project_start_date'], '2025-11-01')
        self.assertEqual(job_data['project_end_date'], '2026-05-31')
        self.assertEqual(job_data['compensation_type'], 'Fixed')
        self.assertEqual(job_data['compensation_amount'], 'Birr50,000')
        self.assertEqual(job_data['project_details'], 'Full production of a feature film')
        self.assertTrue('created_at' in job_data)

    def test_get_jobs_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_job(self):
        data = {
            'talents': 'New Talent',
            'project_type': 'Theater',
            'organization_type': 'Nonprofit',
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'New Company',
            'company_website': 'https://newcompany.com',
            'job_title': 'Director',
            'country': 'Canada',
            'postal_code': 'M5V 2T6',
            'project_title': 'New Project',
            'project_start_date': '2025-12-01',
            'project_end_date': '2026-06-30',
            'compensation_type': 'Hourly',
            'compensation_amount': 'Birr75/hour',
            'project_details': 'A new theater production'
        }
        response = self.client.post('/api/jobs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Job created successfully.')
        self.assertTrue('id' in response.data)
        job = Job.objects.get(id=response.data['id'])
        self.assertEqual(job.talents, 'New Talent')
        self.assertEqual(job.project_title, 'New Project')
        self.assertEqual(job.project_start_date, date(2025, 12, 1))
        self.assertEqual(job.compensation_type, 'Hourly')

    def test_create_job_missing_required_fields(self):
        data = {
            'project_type': 'Theater',
            'organization_type': 'Nonprofit'
        }
        response = self.client.post('/api/jobs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('talents', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('company_name', response.data)
        self.assertIn('job_title', response.data)
        self.assertIn('country', response.data)

    def test_create_job_unauthenticated(self):
        self.client.credentials()
        data = {
            'talents': 'New Talent',
            'project_type': 'Theater',
            'organization_type': 'Nonprofit',
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'New Company',
            'job_title': 'Director',
            'country': 'Canada'
        }
        response = self.client.post('/api/jobs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_job(self):
        data = {
            'talents': 'Updated Talent',
            'project_type': 'Updated Film',
            'organization_type': 'Updated Company',
            'first_name': 'Updated',
            'last_name': 'Name',
            'company_name': 'Updated Inc.',
            'company_website': 'https://example.com/updated',
            'job_title': 'Updated Director',
            'country': 'Updated Country',
            'postal_code': '90211',
            'project_title': 'Updated Movie Project',
            'project_start_date': '2025-12-01',
            'project_end_date': '2026-06-30',
            'compensation_type': 'Hourly',
            'compensation_amount': 'Birr75/hour',
            'project_details': 'Updated production details'
        }
        response = self.client.put(f'/api/jobs/{self.job.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Job updated successfully.')
        self.assertEqual(response.data['id'], self.job.id)
        self.job.refresh_from_db()
        self.assertEqual(self.job.talents, 'Updated Talent')
        self.assertEqual(self.job.project_title, 'Updated Movie Project')
        self.assertEqual(self.job.project_start_date, date(2025, 12, 1))
        self.assertEqual(self.job.project_end_date, date(2026, 6, 30))
        self.assertEqual(self.job.compensation_type, 'Hourly')
        self.assertEqual(self.job.compensation_amount, 'Birr75/hour')
        self.assertEqual(self.job.project_details, 'Updated production details')

    def test_update_job_not_found(self):
        data = {
            'talents': 'Updated Talent'
        }
        response = self.client.put('/api/jobs/999/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'Job not found.')

    def test_update_job_unauthenticated(self):
        self.client.credentials()
        data = {
            'talents': 'Updated Talent'
        }
        response = self.client.put(f'/api/jobs/{self.job.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_job(self):
        response = self.client.delete(f'/api/jobs/{self.job.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Job deleted successfully.')
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_delete_job_not_found(self):
        response = self.client.delete('/api/jobs/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'Job not found.')

    def test_delete_job_unauthenticated(self):
        self.client.credentials()
        response = self.client.delete(f'/api/jobs/{self.job.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)