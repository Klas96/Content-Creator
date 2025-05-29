import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid # Import uuid for generating task IDs if needed for direct task manipulation
import time # To simulate processing

# Adjust the import path if your api.py is structured differently
from api import app, tasks, VideoRequest # Import VideoRequest for POST payload

# Fixture for the TestClient
@pytest.fixture(scope="module")
def client():
    # If there's any app setup that happens on startup (like loading models),
    # ensure it's compatible with testing or can be mocked.
    return TestClient(app)

# Fixture to clear the tasks dictionary before each test
@pytest.fixture(autouse=True)
def clear_tasks_dict_before_each_test():
    tasks.clear()

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Video Generation API is running."}

@patch('api.run_video_creation') # Patch where the function is LOOKED UP (in api.py)
def test_create_video_task_success(mock_run_video_creation, client):
    # Mock the background task function directly
    # It won't actually run in the background with TestClient in this setup,
    # but we can simulate its effect on the `tasks` dict or test its invocation.
    
    character_desc = "A brave knight"
    response = client.post("/videos", json={"character_description": character_desc})
    
    assert response.status_code == 200
    json_response = response.json()
    task_id = json_response.get("task_id")
    
    assert task_id is not None
    assert json_response == {
        "task_id": task_id,
        "status": "processing",
        "message": "Video generation task started."
    }
    
    # Check if the background task was called (or would have been)
    # For BackgroundTasks, direct assertion of call is tricky without more setup.
    # Instead, we verify the state it's supposed to create.
    assert task_id in tasks
    assert tasks[task_id]["status"] == "processing"
    
    # To verify mock_run_video_creation was added to background_tasks:
    # This requires deeper FastAPI/Starlette BackgroundTasks knowledge or a different mocking strategy.
    # For now, we focus on the state change in `tasks` as a proxy.
    # If `run_video_creation` was called directly (not as a background task), you'd do:
    # mock_run_video_creation.assert_called_once_with(task_id, character_desc)


def test_get_video_status_processing(client):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}
    
    response = client.get(f"/videos/{task_id}")
    assert response.status_code == 200
    assert response.json() == {
        "task_id": task_id,
        "status": "processing",
        "video_path": None,
        "error": None
        # "details" field is optional, so it might be missing if None, which is fine
        # If it must be present as null, the endpoint or TaskStatusResponse needs adjustment
    }

# To test completed/failed states, we need to simulate the background task finishing.
# We can do this by manually setting the task state after the POST,
# or by directly calling and mocking the `run_video_creation` logic.

@patch('api.create_video_task') # Patching the core logic function
def test_get_video_status_completed(mock_create_video, client):
    # Simulate task creation via POST
    character_desc = "A wise wizard"
    post_response = client.post("/videos", json={"character_description": character_desc})
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    # Simulate successful completion by the (mocked) background task
    expected_video_path = "output/mock_video.mp4"
    mock_create_video.return_value = expected_video_path
    
    # Manually update the task status as the background task would
    # This is a simplified way to test; for true background task testing,
    # you might need tools like `fastapi.BackgroundTasks` with `asyncio.sleep`
    # or a more robust task queue testing setup.
    tasks[task_id] = {"status": "completed", "video_path": expected_video_path}
    
    response = client.get(f"/videos/{task_id}")
    assert response.status_code == 200
    # Add "details": None if your response model strictly requires it,
    # or ensure Pydantic handles Optional fields correctly by omitting them if None.
    # Based on current TaskStatusResponse, if details is not provided, it's fine.
    assert response.json() == {
        "task_id": task_id,
        "status": "completed",
        "video_path": expected_video_path,
        "error": None
    }
    # If run_video_creation was called directly by post endpoint (not background):
    # mock_create_video.assert_called_once_with(character_desc)


@patch('api.create_video_task') # Patching the core logic function
def test_get_video_status_failed(mock_create_video, client):
    character_desc = "A clumsy dragon"
    post_response = client.post("/videos", json={"character_description": character_desc})
    assert post_response.status_code == 200
    task_id = post_response.json()["task_id"]

    # Simulate failure by the (mocked) background task
    error_message = "Failed to generate story"
    mock_create_video.side_effect = Exception(error_message)

    # Manually update task status to reflect failure
    tasks[task_id] = {"status": "failed", "error": error_message}
        
    response = client.get(f"/videos/{task_id}")
    assert response.status_code == 200
    assert response.json() == {
        "task_id": task_id,
        "status": "failed",
        "video_path": None,
        "error": error_message
    }

def test_get_video_status_not_found(client):
    non_existent_task_id = str(uuid.uuid4())
    response = client.get(f"/videos/{non_existent_task_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": f"Task with ID '{non_existent_task_id}' not found."}

# It's good practice to also test edge cases for the POST request if any,
# e.g., invalid payload, though Pydantic handles some of this automatically.
def test_create_video_task_invalid_payload(client):
    response = client.post("/videos", json={"wrong_field": "A brave knight"})
    assert response.status_code == 422  # Unprocessable Entity from Pydantic

# A note on the 'details' field in TaskStatusResponse:
# Pydantic models by default omit fields that are None and not explicitly set.
# If the API returns a field as `null`, then the expected JSON should include `"details": null`.
# If the field is simply omitted when its value is None, then the current assertions are correct
# (i.e. not including `details` in the expected dictionary).
# The current `get_video_status` in `api.py` returns:
# { "task_id": task_id, "status": task["status"], "video_path": task.get("video_path"), "error": task.get("error") }
# This means 'details' will indeed be omitted if not present in the `task` dictionary.
# So, the test assertions are consistent with the current `api.py` implementation.
# If `TaskStatusResponse` had `details: Optional[Dict[str, Any]] = Field(default=None)` or similar to force output,
# then tests would need `"details": None`.
# For now, this is consistent.
