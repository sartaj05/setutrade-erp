import json
from django.contrib.auth.models import User
from django.test import Client, TestCase
from .models import Profile


class ApiSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner-test',
            email='owner-test@example.com',
            password='test-password-123',
            first_name='Owner',
        )
        Profile.objects.create(user=self.user, role='OWNER', business_name='Test Distribution Co.')

    def test_health(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_login_returns_role_and_token(self):
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'email': self.user.email, 'password': 'test-password-123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['user']['role'], 'OWNER')
        self.assertIn('purchases', payload['user']['permissions'])
        self.assertIn('insights', payload['user']['permissions'])
        self.assertTrue(payload['token'])
