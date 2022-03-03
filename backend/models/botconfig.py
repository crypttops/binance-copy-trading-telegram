from db import db
from .helpers import BaseClass
from datetime import datetime

class BotConfigsModel(BaseClass, db.Model):
    __tablename__="botconfigs"
    id:int
    telegram_id:str
    key:str
    secret:str
    amount:float
    leverage:int
    registered_on:str
    updated_on:str
    subscribed:bool
    subscription_type:str
    subscription_start_date:str
    subscription_end_date:str
    
    id =db.Column(db.Integer, primary_key=True, autoincrement= True)
    telegram_id = db.Column(db.String, nullable=False)
    key = db.Column(db.Text, unique=True, nullable=False)
    secret = db.Column(db.Text, unique=True, nullable=False)
    amount = db.Column(db.Float(), nullable=True)
    leverage = db.Column(db.Integer, nullable=False, default=20)
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
    
    