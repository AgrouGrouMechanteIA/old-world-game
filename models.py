from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('PlayerProfile', uselist=False, back_populates='user')

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    is_city = db.Column(db.Boolean, default=False)
    has_market = db.Column(db.Boolean, default=False)
    region = db.Column(db.String(80))
    local_resource = db.Column(db.String(200), nullable=True)
    colonisable = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)

class PlayerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='profile')
    pounds = db.Column(db.Integer, default=0)
    shillings = db.Column(db.Integer, default=0)
    hunger = db.Column(db.Integer, default=0)
    health = db.Column(db.Integer, default=5)
    level = db.Column(db.Integer, default=1)
    location_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=True)
    location = db.relationship('Place')
    property_count = db.Column(db.Integer, default=0)
    last_task_turn = db.Column(db.String(20), nullable=True)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    property_type = db.Column(db.String(80), default='field')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ItemType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(140), nullable=False)
    edible_hunger = db.Column(db.Integer, default=0)
    edible_health = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, default='')
    craft_recipe = db.Column(JSON, nullable=True)

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    amount = db.Column(db.Integer, default=0)
    item_type = db.relationship('ItemType')

class Mail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_player = db.Column(db.Integer, db.ForeignKey('player_profile.id'))
    to_player = db.Column(db.Integer, db.ForeignKey('player_profile.id'))
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class MarketListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    amount = db.Column(db.Integer, default=0)
    price_pounds = db.Column(db.Integer, default=0)
    price_shillings = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    task_type = db.Column(db.String(200), nullable=False)
    metadata_json = db.Column(JSON, nullable=True)   # renamed to avoid reserved 'metadata'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    turn_date = db.Column(db.String(20), nullable=False)

class HarvestTimer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    item_type_key = db.Column(db.String(80), nullable=False)
    planted_turn = db.Column(db.String(20), nullable=False)
    ready_in_turns = db.Column(db.Integer, default=4)
    amount_min = db.Column(db.Integer, default=1)
    amount_max = db.Column(db.Integer, default=1)
    done = db.Column(db.Boolean, default=False)

class Turn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_key = db.Column(db.String(20), unique=True, nullable=False)
    processed = db.Column(db.Boolean, default=False)

class BoatStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_index = db.Column(db.Integer, default=0)
    stuck_counter = db.Column(db.Integer, default=0)
    route = db.Column(JSON, default=list)
