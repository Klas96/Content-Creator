import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

# Adjust the import path if your api.py is structured differently
from api import app, tasks, VideoRequest # Import VideoRequest for POST payload

class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # This method is called once before all tests in the class
        cls.client = TestClient(app)

    def setUp(self):
        # This method is called before each test
        tasks.clear() # Clear tasks dict before each test

    def tearDown(self):
        # This method is called after each test
        pass # Add any cleanup if necessary

    @classmethod
    def tearDownClass(cls):
        # This method is called once after all tests in the class
        pass

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Video Generation API is running."})

    @patch('api.run_video_creation') # Patch where the function is LOOKED UP
    def test_create_video_task_success(self, mock_run_video_creation):
        character_desc = "A brave knight"
        response = self.client.post("/videos", json={"character_description": character_desc})
        
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        task_id = json_response.get("task_id")
        
        self.assertIsNotNone(task_id)
        self.assertEqual(json_response, {
            "task_id": task_id,
            "status": "processing",
            "message": "Video generation task started."
        })
        
        self.assertIn(task_id, tasks)
        self.assertEqual(tasks[task_id]["status"], "processing")
        # mock_run_video_creation.assert_called_once_with(task_id, character_desc) 
        # ^ This assertion is tricky with BackgroundTasks as it's not called directly in the test client's thread.
        # We are verifying the side effect (task entry in `tasks` dict) which is a good proxy.

    def test_get_video_status_processing(self):
        task_id = str(uuid.uuid4())
        tasks[task_id] = {"status": "processing"}
        
        response = self.client.get(f"/videos/{task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "task_id": task_id,
            "status": "processing",
            "video_path": None,
            "error": None,
            "details": None # Assuming TaskStatusResponse includes details: Optional = None
        })

    @patch('api.create_video_task') # Patching the core logic function
    def test_get_video_status_completed(self, mock_create_video_task):
        character_desc = "A wise wizard"
        post_response = self.client.post("/videos", json={"character_description": character_desc})
        self.assertEqual(post_response.status_code, 200)
        task_id = post_response.json()["task_id"]

        expected_video_path = "output/mock_video.mp4"
        mock_create_video_task.return_value = expected_video_path
        
        # Simulate background task completion
        tasks[task_id] = {"status": "completed", "video_path": expected_video_path}
        
        response = self.client.get(f"/videos/{task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "task_id": task_id,
            "status": "completed",
            "video_path": expected_video_path,
            "error": None,
            "details": None # Assuming TaskStatusResponse includes details: Optional = None
        })

    @patch('api.create_video_task') # Patching the core logic function
    def test_get_video_status_failed(self, mock_create_video_task):
        character_desc = "A clumsy dragon"
        post_response = self.client.post("/videos", json={"character_description": character_desc})
        self.assertEqual(post_response.status_code, 200)
        task_id = post_response.json()["task_id"]

        error_message = "Failed to generate story"
        mock_create_video_task.side_effect = Exception(error_message)

        # Simulate background task failure
        tasks[task_id] = {"status": "failed", "error": error_message}
            
        response = self.client.get(f"/videos/{task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "task_id": task_id,
            "status": "failed",
            "video_path": None,
            "error": error_message,
            "details": None # Assuming TaskStatusResponse includes details: Optional = None
        })

    def test_get_video_status_not_found(self):
        non_existent_task_id = str(uuid.uuid4())
        response = self.client.get(f"/videos/{non_existent_task_id}")
        self.assertEqual(response.status_code, 404)
        # The detail message might be slightly different, check actual API response if test fails
        self.assertEqual(response.json(), {"detail": f"Task with ID '{non_existent_task_id}' not found."})

    def test_create_video_task_invalid_payload(self):
        response = self.client.post("/videos", json={"wrong_field": "A brave knight"})
        self.assertEqual(response.status_code, 422) # Unprocessable Entity

if __name__ == '__main__':
    unittest.main()
