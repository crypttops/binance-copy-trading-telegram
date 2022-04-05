from typing import Dict
from db import db
from backend.models import BotConfigsModel
def getConfigs(telegram_id):
    """Get configuration of a single user"""

    configs = db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).first()
    if configs:
        return configs
    else:
        return None
def getAllUserConfigs():
    """Get all the user configurations"""

    configs = db.session.query(BotConfigsModel).filter_by(subscribed=True,connected=True).all()
    return configs

def dbupdate(telegram_id, data:Dict):
    try:
        db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).update(data)
        db.session.commit()
        return None, True
    except Exception as e:
        return str(e), False
def checkSubscriptionStatus(telegram_id):
    user = db.session.query(BotConfigsModel).filter_by(telegram_id=str(telegram_id)).first()
    if user is not None:
        if user.subscribed ==True:
            return True, user.subscription_type
        else:
            return False, None
    else:
        return False, None
