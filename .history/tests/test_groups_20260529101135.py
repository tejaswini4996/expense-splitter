"""Tests for group management routes"""
import pytest
from fastapi import status

from app.models import Group, User


class TestGroupCreation:
    """Test group creation"""
    
    def test_create_group_success(self, client, access_token: str, test_user: User):
        """Test successful group creation"""
        response = client.post(
            "/api/v1/groups/",
            json={
                "name": "Vacation Trip",
                "description": "Summer trip to Bali",
                "currency": "USD",
                "member_ids": []
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Vacation Trip"
        assert data["description"] == "Summer trip to Bali"
        assert data["created_by"] == test_user.id
    
    def test_create_group_no_token(self, client):
        """Test creating group without authentication"""
        response = client.post(
            "/api/v1/groups/",
            json={
                "name": "Unauthorized Group",
                "currency": "USD"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGroupRetrieval:
    """Test group retrieval"""
    
    def test_list_user_groups(self, client, access_token: str, test_user: User, test_group: Group):
        """Test listing user's groups"""
        response = client.get(
            "/api/v1/groups/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(g["id"] == test_group.id for g in data)
    
    def test_get_group_details(self, client, access_token: str, test_group: Group):
        """Test getting group details"""
        response = client.get(
            f"/api/v1/groups/{test_group.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_group.id
        assert data["name"] == "Test Group"
    
    def test_get_group_not_found(self, client, access_token: str):
        """Test getting nonexistent group"""
        response = client.get(
            "/api/v1/groups/nonexistent-id",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
