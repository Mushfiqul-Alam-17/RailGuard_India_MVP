from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<User {self.username}>"

class TrustID(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    tid_hash = db.Column(db.String(64), unique=True, nullable=False)
    ipfs_cid = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<TrustID {self.tid_hash[:8]}>"

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    train_number = db.Column(db.String(10), nullable=False)
    coach = db.Column(db.String(5), nullable=False)
    seat = db.Column(db.String(5), nullable=False)
    qr_code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), default="valid")
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Ticket {self.train_number}-{self.coach}-{self.seat}>"

class StandingZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    train_number = db.Column(db.String(10), nullable=False)
    coach = db.Column(db.String(5), nullable=False)
    zone = db.Column(db.String(5), nullable=False)
    qr_code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), default="valid")
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<StandingZone {self.train_number}-{self.coach}-{self.zone}>"

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    risk_level = db.Column(db.String(10), default="Low")
    status = db.Column(db.String(20), default="pending")
    resolution = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Complaint {self.id} - {self.risk_level}>"

class Fine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default="issued")
    blockchain_hash = db.Column(db.String(66), nullable=True)
    
    def __repr__(self):
        return f"<Fine {self.id} - Rs.{self.amount}>"

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coach = db.Column(db.String(5), nullable=False)
    seat_number = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(10), default="vacant")
    phone = db.Column(db.String(15), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('coach', 'seat_number'),)
    
    def __repr__(self):
        return f"<Seat {self.coach}-{self.seat_number} ({self.status})>"

class EmergencySlip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    waiver_status = db.Column(db.String(20), default="pending")
    qr_code = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"<EmergencySlip {self.id} - {self.waiver_status}>"

class TTUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    zone = db.Column(db.String(20))
    division = db.Column(db.String(30))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<TTUser {self.username} - {self.employee_id}>"

class TTLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tt_id = db.Column(db.Integer, db.ForeignKey('tt_user.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    passenger_phone = db.Column(db.String(15))
    train_number = db.Column(db.String(10))
    coach = db.Column(db.String(5))
    location = db.Column(db.String(100))
    
    tt = db.relationship('TTUser', backref=db.backref('logs', lazy=True))
    
    def __repr__(self):
        return f"<TTLog {self.id} - {self.action}>"

class EmergencyAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    train_number = db.Column(db.String(10))
    coach = db.Column(db.String(5))
    status = db.Column(db.String(20), default="pending")
    resolved_by = db.Column(db.Integer, db.ForeignKey('tt_user.id'))
    resolved_at = db.Column(db.DateTime)
    
    resolver = db.relationship('TTUser', backref=db.backref('resolved_alerts', lazy=True))
    
    def __repr__(self):
        return f"<EmergencyAlert {self.id} - {self.status}>"
