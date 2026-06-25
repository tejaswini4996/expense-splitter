"""Tests for authentication routes"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models import User
from app.security import SecurityUtils


class TestUserRegistration:
    """Test user registration"""
    
    def test_register_new_user(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "secure_password_123"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["full_name"] == "New User"
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_user: User):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "different_username",
                "full_name": "Another User",
                "password": "secure_password_123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]
    
    def test_register_short_password(self, client):
        """Test registration with short password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "short"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """Test user login"""
    
    def test_login_success(self, client, test_user: User):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "test_password_123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_wrong_password(self, client, test_user: User):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "any_password"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Test get current user endpoint"""
    
    def test_get_current_user_success(self, client, test_user: User, access_token: str):
        """Test getting current user info"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
