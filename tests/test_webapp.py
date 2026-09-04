"""
Integration test for Flask Web Application endpoints.
"""

import unittest
from app import app

class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Savings Goal Agent', response.data)

    def test_get_progress_endpoint(self):
        response = self.app.get('/api/progress')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('target', json_data)
        self.assertIn('saved', json_data)

    def test_chat_endpoint_create_goal(self):
        response = self.app.post('/api/chat', json={"message": "I want to save ₹60,000 by December."})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('final_answer', json_data)
        self.assertIn('trace_log', json_data)
        self.assertIn('progress', json_data)
        self.assertEqual(json_data['progress']['target'], 60000.0)

    def test_chat_endpoint_log_saving(self):
        # Create goal first
        self.app.post('/api/chat', json={"message": "I want to save ₹60,000 by December."})
        # Log saving
        response = self.app.post('/api/chat', json={"message": "I saved ₹5,000."})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['progress']['saved'], 5000.0)
        self.assertEqual(json_data['progress']['remaining'], 55000.0)

    def test_reset_endpoint(self):
        response = self.app.post('/api/reset')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['success'])

if __name__ == '__main__':
    unittest.main()
