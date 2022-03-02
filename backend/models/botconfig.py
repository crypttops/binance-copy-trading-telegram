from db import db
from .helpers import BaseClass
from datetime import datetime

class BotConfigsModel(BaseClass, db.Model):
    __tablename__="botconfigs"
    telegram_id:int
    key:str
    secret:str
    amount:float
    registered_on:str
    updated_on:str

    telegram_id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, unique=True, nullable=False)
    secret = db.Column(db.Text, unique=True, nullable=False)
    amount = db.Column(db.Float(), nullable=True)
    registered_on = db.Column(db.DateTime, nullable=True)
    subscribed= db.Column(db.Boolean, default=False)
    subscription_type=db.Column(db.String, nullable=True)
    subscription_start_date = db.Column(db.DateTime, nullable=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    updated_on = db.Column(db.DateTime, nullable=True)
  

    @classmethod
    def create(cls, **kw):
        obj = cls(**kw)
        db.session.add(obj)
        db.session.commit()
    
    