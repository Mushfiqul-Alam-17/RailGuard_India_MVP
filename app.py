import os
import logging
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define base model class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "railguard_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///railguard.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with SQLAlchemy
db.init_app(app)

# Import routes and models
with app.app_context():
    # Import models
    from models import User, Ticket, TrustID, Complaint, Fine, Seat, StandingZone, EmergencySlip
    
    # Create all database tables
    db.create_all()
    
    # Import utility modules
    from utils.sms import send_sms_notification
    from utils.qr_code import generate_qr_code
    from utils.blockchain import create_trust_id
    from utils.ai import analyze_complaint_risk

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/complaint-heatmap")
def complaint_heatmap():
    """Display complaint heatmap dashboard"""
    # Check if admin or TT is logged in
    is_admin = session.get("is_admin", False)
    is_tt = "tt_id" in session
    
    if not (is_admin or is_tt):
        flash("You must be logged in as an admin or TT to view this page", "warning")
        return redirect(url_for("tt_login"))
    
    # Generate mock top risk routes
    top_routes = [
        {
            "route": "Delhi - Lucknow",
            "trains": "12533, 12429",
            "complaints": 45,
            "risk_score": 85
        },
        {
            "route": "Mumbai - Pune",
            "trains": "12123, 12126",
            "complaints": 32,
            "risk_score": 65
        },
        {
            "route": "Chennai - Bangalore",
            "trains": "12639, 12640",
            "complaints": 28,
            "risk_score": 55
        },
        {
            "route": "Kolkata - Patna",
            "trains": "12301, 12302",
            "complaints": 37,
            "risk_score": 75
        },
        {
            "route": "Hyderabad - Vijayawada",
            "trains": "12723, 12724",
            "complaints": 24,
            "risk_score": 45
        }
    ]
    
    return render_template("complaint_heatmap.html", top_routes=top_routes)

@app.route("/dashboard")
def dashboard():
    # Get counts for dashboard
    complaint_count = Complaint.query.count()
    high_risk_complaints = Complaint.query.filter_by(risk_level="High").count()
    ticket_count = Ticket.query.count()
    trust_id_count = TrustID.query.count()
    standing_count = StandingZone.query.count()
    
    return render_template("dashboard.html", 
                           complaint_count=complaint_count,
                           high_risk_complaints=high_risk_complaints,
                           ticket_count=ticket_count,
                           trust_id_count=trust_id_count,
                           standing_count=standing_count)

# Complaint system routes
@app.route("/complaints", methods=["GET", "POST"])
def complaints():
    if request.method == "POST":
        phone = request.form.get("phone")
        message = request.form.get("message")
        
        if not phone or not message:
            flash("Phone number and message are required", "danger")
            return redirect(url_for("complaints"))
        
        # Analyze complaint risk using AI
        risk_level = analyze_complaint_risk(message)
        
        # Create and save complaint
        new_complaint = Complaint(
            phone=phone,
            message=message,
            timestamp=datetime.now(),
            risk_level=risk_level
        )
        db.session.add(new_complaint)
        db.session.commit()
        
        # Send confirmation SMS
        try:
            send_sms_notification(
                phone, 
                f"Your complaint has been registered. Risk level: {risk_level}. We'll take action accordingly."
            )
            flash("Complaint submitted successfully", "success")
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            flash("Complaint submitted but SMS notification failed", "warning")
        
        return redirect(url_for("complaints"))
    
    # GET request - display all complaints
    complaints_list = Complaint.query.order_by(Complaint.timestamp.desc()).all()
    return render_template("complaints.html", complaints=complaints_list)

# Trust ID routes
@app.route("/trust-id", methods=["GET", "POST"])
def trust_id():
    if request.method == "POST":
        phone = request.form.get("phone")
        aadhaar = request.form.get("aadhaar", "")  # Optional
        
        if not phone:
            flash("Phone number is required", "danger")
            return redirect(url_for("trust_id"))
        
        # Check if Trust ID already exists
        existing_id = TrustID.query.filter_by(phone=phone).first()
        if existing_id:
            flash("Trust ID already exists for this phone number", "warning")
            return redirect(url_for("trust_id"))
        
        # Generate Trust ID using blockchain
        tid_hash, ipfs_cid = create_trust_id(phone, aadhaar)
        
        # Save Trust ID
        new_tid = TrustID(
            phone=phone,
            tid_hash=tid_hash,
            ipfs_cid=ipfs_cid,
            created_at=datetime.now()
        )
        db.session.add(new_tid)
        db.session.commit()
        
        flash("Trust ID created successfully", "success")
        return redirect(url_for("trust_id"))
    
    # GET request - display all Trust IDs
    trust_ids = TrustID.query.order_by(TrustID.created_at.desc()).all()
    return render_template("trust_id.html", trust_ids=trust_ids)

# Ticket and QR code routes
@app.route("/ticket", methods=["GET", "POST"])
def ticket():
    if request.method == "POST":
        phone = request.form.get("phone")
        train_number = request.form.get("train_number")
        coach = request.form.get("coach")
        seat = request.form.get("seat")
        
        if not all([phone, train_number, coach, seat]):
            flash("All fields are required", "danger")
            return redirect(url_for("ticket"))
        
        # Check if Trust ID exists
        trust_id = TrustID.query.filter_by(phone=phone).first()
        if not trust_id:
            flash("Trust ID not found for this phone number. Please create one first.", "warning")
            return redirect(url_for("trust_id"))
        
        # Generate QR code
        ticket_data = f"{train_number}|{coach}|{seat}|{phone}"
        qr_code = generate_qr_code(ticket_data)
        
        # Create and save ticket
        new_ticket = Ticket(
            phone=phone,
            train_number=train_number,
            coach=coach,
            seat=seat,
            qr_code=qr_code,
            created_at=datetime.now(),
            status="valid"
        )
        db.session.add(new_ticket)
        
        # Update seat status
        seat_record = Seat.query.filter_by(coach=coach, seat_number=seat).first()
        if not seat_record:
            seat_record = Seat(coach=coach, seat_number=seat, status="occupied", phone=phone)
            db.session.add(seat_record)
        else:
            seat_record.status = "occupied"
            seat_record.phone = phone
            
        db.session.commit()
        
        flash("Ticket generated successfully", "success")
        return redirect(url_for("ticket", ticket_id=new_ticket.id))
    
    # GET request - display ticket if ID provided, else form
    ticket_id = request.args.get("ticket_id")
    if ticket_id:
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            return render_template("ticket.html", ticket=ticket, qr_code=ticket.qr_code)
    
    # Display all tickets
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template("ticket.html", tickets=tickets)

# Standing Zone routes
@app.route("/standing-zone", methods=["GET", "POST"])
def standing_zone():
    if request.method == "POST":
        phone = request.form.get("phone")
        train_number = request.form.get("train_number")
        coach = request.form.get("coach")
        zone = request.form.get("zone")
        
        if not all([phone, train_number, coach, zone]):
            flash("All fields are required", "danger")
            return redirect(url_for("standing_zone"))
        
        # Check if Trust ID exists
        trust_id = TrustID.query.filter_by(phone=phone).first()
        if not trust_id:
            flash("Trust ID not found for this phone number. Please create one first.", "warning")
            return redirect(url_for("trust_id"))
        
        # Generate QR code for standing zone
        zone_data = f"{train_number}|{coach}|{zone}|{phone}"
        qr_code = generate_qr_code(zone_data)
        
        # Create and save standing zone allocation
        new_zone = StandingZone(
            phone=phone,
            train_number=train_number,
            coach=coach,
            zone=zone,
            qr_code=qr_code,
            created_at=datetime.now(),
            status="valid"
        )
        db.session.add(new_zone)
        db.session.commit()
        
        flash("Standing zone QR code generated successfully", "success")
        return redirect(url_for("standing_zone", zone_id=new_zone.id))
    
    # GET request - display zone if ID provided, else form
    zone_id = request.args.get("zone_id")
    if zone_id:
        zone = StandingZone.query.get(zone_id)
        if zone:
            return render_template("standing_zone.html", zone=zone, qr_code=zone.qr_code)
    
    # Display all standing zones
    zones = StandingZone.query.order_by(StandingZone.created_at.desc()).all()
    return render_template("standing_zone.html", zones=zones)

# Seat Management routes
@app.route("/seat-management", methods=["GET", "POST"])
def seat_management():
    if request.method == "POST":
        coach = request.form.get("coach")
        seat_number = request.form.get("seat_number")
        status = request.form.get("status")
        phone = request.form.get("phone", "")
        
        if not all([coach, seat_number, status]):
            flash("Coach, seat number, and status are required", "danger")
            return redirect(url_for("seat_management"))
        
        # Find or create seat
        seat = Seat.query.filter_by(coach=coach, seat_number=seat_number).first()
        if seat:
            seat.status = status
            seat.phone = phone if status == "occupied" else ""
        else:
            seat = Seat(
                coach=coach,
                seat_number=seat_number,
                status=status,
                phone=phone if status == "occupied" else ""
            )
            db.session.add(seat)
        
        db.session.commit()
        flash("Seat status updated successfully", "success")
        return redirect(url_for("seat_management"))
    
    # GET request - display all seats
    seats = Seat.query.order_by(Seat.coach, Seat.seat_number).all()
    return render_template("seat_management.html", seats=seats)

# API Endpoints
@app.route("/api/verify-ticket", methods=["POST"])
def verify_ticket():
    data = request.json
    if not data or "ticket_data" not in data:
        return jsonify({"status": "error", "message": "No ticket data provided"}), 400
    
    ticket_data = data["ticket_data"]
    try:
        train_number, coach, seat, phone = ticket_data.split("|")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid ticket format"}), 400
    
    # Check if ticket exists
    ticket = Ticket.query.filter_by(
        train_number=train_number,
        coach=coach,
        seat=seat,
        phone=phone,
        status="valid"
    ).first()
    
    if ticket:
        return jsonify({
            "status": "success",
            "valid": True,
            "ticket": {
                "train_number": train_number,
                "coach": coach,
                "seat": seat,
                "phone": phone[-4:].rjust(10, '*'),  # Mask phone number
                "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        })
    else:
        return jsonify({"status": "success", "valid": False})

@app.route("/api/verify-standing-zone", methods=["POST"])
def verify_standing_zone():
    data = request.json
    if not data or "zone_data" not in data:
        return jsonify({"status": "error", "message": "No zone data provided"}), 400
    
    zone_data = data["zone_data"]
    try:
        train_number, coach, zone, phone = zone_data.split("|")
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid zone format"}), 400
    
    # Check if standing zone allocation exists
    zone_record = StandingZone.query.filter_by(
        train_number=train_number,
        coach=coach,
        zone=zone,
        phone=phone,
        status="valid"
    ).first()
    
    if zone_record:
        return jsonify({
            "status": "success",
            "valid": True,
            "zone": {
                "train_number": train_number,
                "coach": coach,
                "zone": zone,
                "phone": phone[-4:].rjust(10, '*'),  # Mask phone number
                "created_at": zone_record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        })
    else:
        return jsonify({"status": "success", "valid": False})

@app.route("/api/log_verification", methods=["POST"])
def log_verification():
    """Log TT verification activities"""
    if "tt_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated as TT"}), 401
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    # Extract data
    ticket_data = data.get("ticket_data", {})
    action = data.get("action", "Verification action")
    details = data.get("details", "")
    status = data.get("status", "")
    
    # Create log entry
    new_log = TTLog(
        tt_id=session["tt_id"],
        action=action,
        details=details,
        passenger_phone=ticket_data.get("phone", ""),
        train_number=ticket_data.get("train_number", ""),
        coach=ticket_data.get("coach", ""),
        timestamp=datetime.now()
    )
    
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Verification logged successfully",
        "log_id": new_log.id
    })

@app.route("/api/complaints/geo")
def complaints_geo():
    """Get geolocation data for complaints"""
    # In a real implementation, this would query the actual database
    # For now, we'll generate mock data
    import random
    
    # Major Indian cities with coordinates
    cities = [
        {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
        {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
        {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
        {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
        {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
        {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
        {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319},
        {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
        {"name": "Patna", "lat": 25.5941, "lon": 85.1376},
        {"name": "Indore", "lat": 22.7196, "lon": 75.8577},
        {"name": "Thane", "lat": 19.2183, "lon": 72.9781},
        {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
        {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
        {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812},
        {"name": "Ghaziabad", "lat": 28.6692, "lon": 77.4538},
        {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573}
    ]
    
    # Generate random data points near major cities
    data_points = []
    
    for i in range(150):  # Generate 150 data points
        city = random.choice(cities)
        
        # Add some randomness to the coordinates
        lat = city["lat"] + (random.random() - 0.5) * 0.5
        lon = city["lon"] + (random.random() - 0.5) * 0.5
        
        # Random risk level
        risk_level = random.choices(
            ["High", "Medium", "Low"],
            weights=[0.2, 0.3, 0.5],  # 20% high, 30% medium, 50% low
            k=1
        )[0]
        
        # Generate random train number
        train_number = f"{random.randint(10000, 19999)}"
        
        data_points.append({
            "id": i + 1,
            "lat": lat,
            "lon": lon,
            "risk_level": risk_level,
            "train_number": train_number,
            "location": city["name"],
            "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M")
        })
    
    return jsonify(data_points)

@app.route("/api/verifications/geo")
def verifications_geo():
    """Get geolocation data for ticket verifications"""
    # Similar to complaints/geo, this would be real data in production
    import random
    
    # Major Indian cities with coordinates
    cities = [
        {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
        {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
        {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
        {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
        {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
        {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462}
    ]
    
    # Generate random data points near major cities
    data_points = []
    
    for i in range(200):  # Generate 200 data points
        city = random.choice(cities)
        
        # Add some randomness to the coordinates
        lat = city["lat"] + (random.random() - 0.5) * 0.5
        lon = city["lon"] + (random.random() - 0.5) * 0.5
        
        # Generate random train number
        train_number = f"{random.randint(10000, 19999)}"
        
        data_points.append({
            "id": i + 1,
            "lat": lat,
            "lon": lon,
            "train_number": train_number,
            "location": city["name"],
            "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M")
        })
    
    return jsonify(data_points)

@app.route("/api/submit-complaint", methods=["POST"])
def submit_complaint():
    data = request.json
    if not data or "phone" not in data or "message" not in data:
        return jsonify({"status": "error", "message": "Phone and message are required"}), 400
    
    phone = data["phone"]
    message = data["message"]
    
    # Analyze complaint risk
    risk_level = analyze_complaint_risk(message)
    
    # Create and save complaint
    new_complaint = Complaint(
        phone=phone,
        message=message,
        timestamp=datetime.now(),
        risk_level=risk_level
    )
    db.session.add(new_complaint)
    db.session.commit()
    
    # Send confirmation SMS
    try:
        send_sms_notification(
            phone, 
            f"Your complaint has been registered. Risk level: {risk_level}. We'll take action accordingly."
        )
    except Exception as e:
        logger.error(f"SMS notification failed: {e}")
        return jsonify({
            "status": "warning",
            "message": "Complaint submitted but SMS notification failed",
            "complaint_id": new_complaint.id,
            "risk_level": risk_level
        })
    
    return jsonify({
        "status": "success",
        "message": "Complaint submitted successfully",
        "complaint_id": new_complaint.id,
        "risk_level": risk_level
    })

@app.route("/api/issue-fine", methods=["POST"])
def issue_fine():
    data = request.json
    if not data or "phone" not in data or "amount" not in data or "reason" not in data:
        return jsonify({"status": "error", "message": "Phone, amount, and reason are required"}), 400
    
    phone = data["phone"]
    amount = data["amount"]
    reason = data["reason"]
    
    # Create and save fine
    new_fine = Fine(
        phone=phone,
        amount=amount,
        reason=reason,
        timestamp=datetime.now(),
        status="issued",
        blockchain_hash=f"0x{os.urandom(16).hex()}"  # Mock blockchain hash
    )
    db.session.add(new_fine)
    db.session.commit()
    
    # Send fine notification
    try:
        send_sms_notification(
            phone, 
            f"A fine of Rs. {amount} has been issued to you for: {reason}. Fine ID: {new_fine.id}"
        )
    except Exception as e:
        logger.error(f"SMS notification failed: {e}")
    
    return jsonify({
        "status": "success",
        "message": "Fine issued successfully",
        "fine_id": new_fine.id
    })

# Facial verification route
@app.route("/facial-verification")
def facial_verification():
    return render_template("facial_verification.html")

@app.route("/api/register-face", methods=["POST"])
def register_face():
    data = request.json
    if not data or "phone" not in data or "image_data" not in data:
        return jsonify({"success": False, "message": "Phone and image data are required"}), 400
    
    phone = data["phone"]
    image_data = data["image_data"]
    
    # Remove data URL prefix
    if image_data.startswith('data:image'):
        image_data = image_data.split(',')[1]
    
    # Convert base64 to binary
    import base64
    image_binary = base64.b64decode(image_data)
    
    # Import BiometricVerifier
    from utils.biometrics import BiometricVerifier
    
    # Create instance if not exists
    if not hasattr(app, 'biometric_verifier'):
        app.biometric_verifier = BiometricVerifier()
    
    # Register face
    success = app.biometric_verifier.register_face(phone, image_binary)
    
    if success:
        # Emit event for real-time updates
        socketio.emit('trust_id_update', {'phone': phone, 'has_face': True})
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Failed to detect face in image"})

@app.route("/api/check-biometrics", methods=["GET"])
def check_biometrics():
    # Import to check if face_recognition is available
    from utils.biometrics import FACE_RECOGNITION_AVAILABLE
    
    return jsonify({
        "face_recognition_available": FACE_RECOGNITION_AVAILABLE,
        "mode": "face_recognition" if FACE_RECOGNITION_AVAILABLE else "hash_based"
    })

@app.route("/api/verify-face", methods=["POST"])
def verify_face():
    data = request.json
    if not data or "phone" not in data or "image_data" not in data:
        return jsonify({"success": False, "message": "Phone and image data are required"}), 400
    
    phone = data["phone"]
    image_data = data["image_data"]
    
    # Remove data URL prefix
    if image_data.startswith('data:image'):
        image_data = image_data.split(',')[1]
    
    # Convert base64 to binary
    import base64
    image_binary = base64.b64decode(image_data)
    
    # Import BiometricVerifier
    from utils.biometrics import BiometricVerifier
    
    # Check if BiometricVerifier exists
    if not hasattr(app, 'biometric_verifier'):
        app.biometric_verifier = BiometricVerifier()
        return jsonify({"verified": False, "message": "No face registered for this phone"})
    
    # Verify face
    try:
        verification_result = app.biometric_verifier.verify_face(phone, image_binary)
        # Explicitly cast to Python native bool to ensure it's serializable
        verified = True if verification_result else False
        
        # Emit event for real-time updates (ensure all values are primitive types)
        socketio.emit('face_verification_result', {
            'phone': str(phone), 
            'verified': str(verified).lower()  # Convert to string "true" or "false" for JSON safety
        })
        
        # Return result as JSON
        return jsonify({
            "verified": verified,
            "success": True
        })
    except Exception as e:
        app.logger.error(f"Face verification error: {str(e)}")
        return jsonify({
            "verified": False,
            "success": False,
            "message": f"An error occurred during verification: {str(e)}"
        }), 500

# TT Login and Dashboard Routes
@app.route("/tt_login", methods=["GET", "POST"])
def tt_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Username and password are required", "danger")
            return redirect(url_for("tt_login"))
        
        # Check if TT exists and verify password
        tt = TTUser.query.filter_by(username=username).first()
        if tt and check_password_hash(tt.password_hash, password):
            # Set user session
            session["tt_id"] = tt.id
            session["tt_username"] = tt.username
            
            # Update last login
            tt.last_login = datetime.now()
            db.session.commit()
            
            # Log the login action
            new_log = TTLog(
                tt_id=tt.id,
                action="Logged in",
                details="TT login successful",
                timestamp=datetime.now()
            )
            db.session.add(new_log)
            db.session.commit()
            
            flash("Login successful", "success")
            return redirect(url_for("tt_dashboard"))
        
        flash("Invalid username or password", "danger")
        return redirect(url_for("tt_login"))
    
    return render_template("tt_login.html")

@app.route("/tt_dashboard")
def tt_dashboard():
    # Check if TT is logged in
    if "tt_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("tt_login"))
    
    tt_id = session["tt_id"]
    tt_user = TTUser.query.get(tt_id)
    
    if not tt_user:
        session.pop("tt_id", None)
        session.pop("tt_username", None)
        flash("User not found. Please login again", "danger")
        return redirect(url_for("tt_login"))
    
    # Get today's date range
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Get TT statistics
    ticket_logs = TTLog.query.filter_by(tt_id=tt_id, action="Verified ticket").all()
    tickets_verified_today = TTLog.query.filter(
        TTLog.tt_id == tt_id,
        TTLog.action == "Verified ticket",
        TTLog.timestamp.between(today_start, today_end)
    ).count()
    
    standing_logs = TTLog.query.filter_by(tt_id=tt_id, action="Verified standing zone").all()
    standing_zones_today = TTLog.query.filter(
        TTLog.tt_id == tt_id,
        TTLog.action == "Verified standing zone",
        TTLog.timestamp.between(today_start, today_end)
    ).count()
    
    fine_logs = TTLog.query.filter_by(tt_id=tt_id, action="Issued fine").all()
    fine_value = sum(float(log.details.split("₹")[1].split()[0]) for log in fine_logs if "₹" in log.details)
    
    stats = {
        "tickets_verified": len(ticket_logs),
        "tickets_verified_today": tickets_verified_today,
        "standing_zones": len(standing_logs),
        "standing_zones_today": standing_zones_today,
        "fines": len(fine_logs),
        "fine_value": round(fine_value, 2)
    }
    
    # Calculate TT score (simplified for now)
    tt_score = min(100, max(0, 70 + stats["tickets_verified_today"] - stats["fines"]))
    
    # Get recent activity logs
    logs = TTLog.query.filter_by(tt_id=tt_id).order_by(TTLog.timestamp.desc()).limit(10).all()
    
    # Mock performance data for the radar chart
    performance_data = [75, 85, 65, 80, 70]
    
    return render_template("tt_dashboard.html", 
                          tt_user=tt_user, 
                          stats=stats, 
                          logs=logs, 
                          tt_score=tt_score, 
                          performance_data=performance_data)

@app.route("/tt_logout")
def tt_logout():
    if "tt_id" in session:
        tt_id = session["tt_id"]
        
        # Log the logout action
        new_log = TTLog(
            tt_id=tt_id,
            action="Logged out",
            details="TT logout successful",
            timestamp=datetime.now()
        )
        db.session.add(new_log)
        db.session.commit()
        
        # Clear session
        session.pop("tt_id", None)
        session.pop("tt_username", None)
        
        flash("You have been logged out", "success")
    
    return redirect(url_for("tt_login"))

@app.route("/ticket_scanner")
def ticket_scanner():
    if "tt_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("tt_login"))
    
    return render_template("ticket_scanner.html")

@app.route("/issue_fine_form")
def issue_fine_form():
    if "tt_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("tt_login"))
    
    return render_template("issue_fine.html")

@app.route("/sos_alerts")
def sos_alerts():
    if "tt_id" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("tt_login"))
    
    # Get pending SOS alerts
    alerts = EmergencyAlert.query.filter_by(status="pending").order_by(EmergencyAlert.timestamp.desc()).all()
    
    return render_template("sos_alerts.html", alerts=alerts)

# Main entry point
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
