import os

postgres_local_base ='postgresql://postgres:J4c4kPniCpZXhyND7gHQ@containers-us-west-24.railway.app:7102/railway'
# postgres_local_base = os.environ['DATABASE_URL']

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'BinaNceSPoTsWaP')
    DEBUG = False
    TOKEN_EXPIRE_HOURS = 2
    REDIS_URL="redis://default:4sl26m0EmsdiEjUzjoOO@containers-us-west-4.railway.app:6162"
<<<<<<< HEAD
    REDES_SUB_URL=REDIS_URL
=======
    REDES_SUB_URL="redis://default:H5kvgAhlqYVxNEEJ4JZF@containers-us-west-27.railway.app:7558"
>>>>>>> 9218c75fc78ce9585d2356f016aa7d5c4d7da9f3
    BOT_TOKEN="5165033127:AAFVExTGyVh8mH-5goKNV1xO9LCCalAcF0g"
    CELERY_BROKER_URL="redis://default:4sl26m0EmsdiEjUzjoOO@containers-us-west-4.railway.app:6162"

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