# config.py - Flask Configuration
import os
from datetime import timedelta

# Get the base directory path
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration class"""
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "bingo.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # JSON Configuration
    JSON_SORT_KEYS = False
    
    # CORS Configuration
    CORS_HEADERS = 'Content-Type'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Debug mode
    DEBUG = True
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}