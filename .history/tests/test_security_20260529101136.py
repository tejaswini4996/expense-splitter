"""Tests for security utilities"""
import pytest
from datetime import timedelta

from app.security import SecurityUtils


class TestPasswordHashing:
    """Test password hashing"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = SecurityUtils.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_success(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = SecurityUtils.hash_password(password)
        
        assert SecurityUtils.verify_password(password, hashed) == True
    
    def test_verify_password_fail(self):
        """Test password verification with wrong password"""
        password = "test_password_123"
        hashed = SecurityUtils.hash_password(password)
        
        assert SecurityUtils.verify_password("wrong_password", hashed) == False


class TestTokenManagement:
    """Test JWT token management"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test@example.com", "user_id": "user-123"}
        token = SecurityUtils.create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)
    
    def test_verify_token_success(self):
        """Test token verification with valid token"""
        data = {"sub": "test@example.com", "user_id": "user-123"}
        token = SecurityUtils.create_access_token(data)
        
        payload = SecurityUtils.verify_token(token)
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == "user-123"
