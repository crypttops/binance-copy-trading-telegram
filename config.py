import os
from dotenv import load_dotenv
load_dotenv()

postgres_local_base =os.getenv('POSTGRES_URL')
# postgres_local_base = os.environ['DATABASE_URL']

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'BinaNceSPoTsWaP')
    DEBUG = False
    TOKEN_EXPIRE_HOURS = 2
    REDIS_URL=os.getenv('REDIS_URL')
    REDES_SUB_URL=os.getenv('REDES_SUB_URL')
    # BOT_TOKEN="5165033127:AAFVExTGyVh8mH-5goKNV1xO9LCCalAcF0g"
    BOT_TOKEN=os.getenv('BOT_TOKEN')
    CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL')

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = postgres_local_base
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = postgres_local_base
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = postgres_local_base
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig
)

key = Config.SECRET_KEY