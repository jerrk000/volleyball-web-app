from . import db

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    played_matches = db.Column(db.Integer, default=0)
    won_matches = db.Column(db.Integer, default=0)
    lost_matches = db.Column(db.Integer, default=0)

