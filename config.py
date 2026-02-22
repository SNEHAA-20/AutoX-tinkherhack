import os

class Config:
    """Base configuration for SaveSmart application"""
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or "savesmartsecret"
    
    # Database Settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "sqlite:///savesmart.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session Settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Get the config based on environment
ENV = os.environ.get('FLASK_ENV', 'development')

if ENV == 'production':
    config = ProductionConfig
elif ENV == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig
