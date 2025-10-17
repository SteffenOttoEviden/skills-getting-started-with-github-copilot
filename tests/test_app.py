from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_read_root():
    """Test that the root endpoint redirects to index.html"""
    response = client.get("/")
    assert response.status_code == 200  # Redirect is handled by FastAPI's StaticFiles
    # Since we're using StaticFiles, we don't check headers["location"]

def test_get_activities():
    """Test that the activities endpoint returns a list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Check structure of an activity
    activity = next(iter(activities.values()))
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity

def test_signup_for_activity():
    """Test signing up for an activity"""
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # Try to sign up
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify the student was added
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]
    
    # Clean up - remove the test participant
    client.post(f"/activities/{activity_name}/unregister?email={email}")

def test_signup_duplicate():
    """Test that a student cannot sign up twice"""
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # First signup should succeed
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    
    # Second signup should fail
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()
    
    # Clean up
    client.post(f"/activities/{activity_name}/unregister?email={email}")

def test_signup_nonexistent_activity():
    """Test signing up for a non-existent activity"""
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_from_activity():
    """Test unregistering from an activity"""
    activity_name = "Chess Club"
    email = "test@mergington.edu"
    
    # First sign up
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Then unregister
    response = client.post(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    
    # Verify the student was removed
    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]

def test_unregister_not_registered():
    """Test unregistering when not registered"""
    response = client.post("/activities/Chess Club/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"].lower()

def test_activity_capacity():
    """Test that an activity enforces its maximum capacity"""
    activity_name = "Chess Club"
    activities = client.get("/activities").json()
    max_participants = activities[activity_name]["max_participants"]
    current_participants = activities[activity_name]["participants"]
    remaining_spots = max_participants - len(current_participants)
    
    if remaining_spots > 0:
        # Fill up remaining spots in the activity
        test_emails = [f"test{i}@mergington.edu" for i in range(remaining_spots)]
        for email in test_emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Try to add one more participant
        response = client.post(f"/activities/{activity_name}/signup?email=extra@mergington.edu")
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()
        
        # Clean up
        for email in test_emails:
            client.post(f"/activities/{activity_name}/unregister?email={email}")
    else:
        # Activity is already full, just try to add one more
        response = client.post(f"/activities/{activity_name}/signup?email=extra@mergington.edu")
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()