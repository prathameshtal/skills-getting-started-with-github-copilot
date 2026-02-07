"""
Tests for the High School Management System API
"""

import pytest
from fastapi import status


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        
        # Verify some expected activities are present
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Team" in activities
    
    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check Chess Club structure
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        assert chess_club["max_participants"] == 12
    
    def test_get_activities_has_cache_headers(self, client):
        """Test that activities endpoint has no-cache headers"""
        response = client.get("/activities")
        assert "Cache-Control" in response.headers
        assert "no-cache" in response.headers["Cache-Control"]
        assert "no-store" in response.headers["Cache-Control"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signing up for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self, client):
        """Test signing up when already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_with_url_encoded_activity_name(self, client):
        """Test signup with URL encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Programming Class"]["participants"]
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        from urllib.parse import quote
        email = "student+test@mergington.edu"
        response = client.post(
            f"/activities/Art Studio/signup?email={quote(email)}"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Art Studio"]["participants"]


class TestUnregisterParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_unregister_success(self, client):
        """Test successfully unregistering a participant"""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/participants/{email}"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"]
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregistering from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/participants/student@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_participant_not_found(self, client):
        """Test unregistering a participant who is not registered"""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    def test_unregister_with_url_encoded_values(self, client):
        """Test unregister with URL encoded activity name and email"""
        email = "emma@mergington.edu"
        response = client.delete(
            f"/activities/Programming%20Class/participants/{email}"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Programming Class"]["participants"]
    
    def test_unregister_last_participant(self, client):
        """Test unregistering the last participant from an activity"""
        email = "alex@mergington.edu"  # Only participant in Basketball Team
        response = client.delete(
            f"/activities/Basketball Team/participants/{email}"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant was removed and list is now empty
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Basketball Team"]["participants"]
        assert len(activities["Basketball Team"]["participants"]) == 0


class TestIntegrationScenarios:
    """Integration tests for complete user workflows"""
    
    def test_signup_and_unregister_flow(self, client):
        """Test complete flow of signing up and then unregistering"""
        email = "test@mergington.edu"
        activity = "Drama Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify signed up
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify unregistered
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test a student signing up for multiple different activities"""
        email = "multisport@mergington.edu"
        activities_to_join = ["Chess Club", "Swimming Club", "Art Studio"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == status.HTTP_200_OK
        
        # Verify participant is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
    
    def test_participant_count_accuracy(self, client):
        """Test that participant counts remain accurate through operations"""
        activity = "Science Olympiad"
        
        # Get initial count
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity]["participants"])
        assert initial_count == 1
        
        # Add two participants
        client.post(f"/activities/{activity}/signup?email=student1@mergington.edu")
        client.post(f"/activities/{activity}/signup?email=student2@mergington.edu")
        
        # Verify count increased
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == initial_count + 2
        
        # Remove one participant
        client.delete(f"/activities/{activity}/participants/student1@mergington.edu")
        
        # Verify count decreased
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == initial_count + 1
