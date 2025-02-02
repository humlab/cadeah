import json

from flask_testing import TestCase

from middleware import create_app


class ConfigTest(TestCase):
    def create_app(self):
        return create_app()

    def test_ping(self):
        response = self.client.get('/api/ping')

        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertTrue('pong' in data['message'])
        self.assertTrue('success' in data['status'])
