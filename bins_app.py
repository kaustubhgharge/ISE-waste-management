import random
import threading
import time
import os
from flask import Flask, jsonify, request, abort, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from math import radians, cos, sin, sqrt, atan2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bins.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # Disable SQL logs

db = SQLAlchemy(app)
CORS(app)

# --- Models ---
class Bin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100))
    type = db.Column(db.String(50))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    fill = db.Column(db.Integer)
    last_emptied_days_ago = db.Column(db.Integer)
    status = db.Column(db.String(20))


# --- Database Initialization ---
def init_db():
    db.drop_all()
    db.create_all()

    hub = Bin(
        id=0,
        location="PreZero Service HUB",
        type="HUB",
        lat=52.038469,
        lon=8.882418,
        fill=0,
        last_emptied_days_ago=0,
        status='ok'
    )
    db.session.add(hub)

    bins_data = [
        {"id": 1, "location": "Market Square", "type": "Paper", "lat": 52.0257, "lon": 8.8969},
        {"id": 2, "location": "Main Street", "type": "Glass", "lat": 52.0272, "lon": 8.8999},
        {"id": 3, "location": "Train Station", "type": "Organic", "lat": 52.0255, "lon": 8.8948},
        {"id": 4, "location": "City Library", "type": "Paper", "lat": 52.0279, "lon": 8.8947},
        {"id": 5, "location": "Town Hall", "type": "Paper", "lat": 52.0245, "lon": 8.9017},
        {"id": 6, "location": "Museum", "type": "Paper", "lat": 52.0309, "lon": 8.8965},
        {"id": 7, "location": "Central Park", "type": "Plastic", "lat": 52.0311, "lon": 8.8973},
        {"id": 8, "location": "Shopping Mall", "type": "Glass", "lat": 52.0313, "lon": 8.8950},
        {"id": 9, "location": "Community Center", "type": "Plastic", "lat": 52.0315, "lon": 8.8923},
        {"id": 10, "location": "Library Road", "type": "Glass", "lat": 52.0285, "lon": 8.8930},
        {"id": 11, "location": "Church Lane", "type": "Organic", "lat": 52.0262, "lon": 8.8901},
        {"id": 12, "location": "Fire Station", "type": "Glass", "lat": 52.0281, "lon": 8.8919},
        {"id": 13, "location": "Stadium Road", "type": "Plastic", "lat": 52.0302, "lon": 8.8898},
        {"id": 14, "location": "University Avenue", "type": "Paper", "lat": 52.0325, "lon": 8.8953},
        {"id": 15, "location": "Hospital Grounds", "type": "Plastic", "lat": 52.0334, "lon": 8.8941},
        {"id": 16, "location": "Bridge Street", "type": "Glass", "lat": 52.0341, "lon": 8.8961},
        {"id": 17, "location": "East Park", "type": "Organic", "lat": 52.0350, "lon": 8.8975},
        {"id": 18, "location": "West End", "type": "Glass", "lat": 52.0363, "lon": 8.8988},
        {"id": 19, "location": "Railway Crossing", "type": "Plastic", "lat": 52.0306, "lon": 8.9001},
        {"id": 20, "location": "Main Street 2", "type": "Paper", "lat": 52.0312, "lon": 8.8968},
    ]

    for b in bins_data:
        bin_obj = Bin(**b, fill=0, last_emptied_days_ago=0, status='ok')
        db.session.add(bin_obj)

    db.session.commit()


# --- Status Updater ---
def update_bin_statuses(thresholds):
    bins = Bin.query.all()
    for bin in bins:
        if bin.last_emptied_days_ago > thresholds['inactive']:
            bin.status = 'inactive'
        elif bin.fill >= thresholds['full']:
            bin.status = 'full'
        elif bin.fill >= thresholds['nearly_full']:
            bin.status = 'nearly_full'
        else:
            bin.status = 'ok'
    db.session.commit()


# --- Routes ---
@app.route("/")
def serve_dashboard():
    return render_template("dashboard.html")


@app.route('/api/bins')
def get_bins():
    thresholds = {
        'full': int(request.args.get('full', 80)),
        'nearly_full': int(request.args.get('nearly_full', 60)),
        'inactive': int(request.args.get('inactive', 7)),
    }
    update_bin_statuses(thresholds)
    bins = Bin.query.all()
    return jsonify([
        {
            'id': b.id,
            'location': b.location,
            'type': b.type,
            'lat': b.lat,
            'lon': b.lon,
            'fill': b.fill,
            'last_emptied_days_ago': b.last_emptied_days_ago,
            'status': b.status,
        } for b in bins
    ])


@app.route('/api/bin/<int:bin_id>')
def get_bin(bin_id):
    bin = Bin.query.get(bin_id)
    if not bin:
        abort(404, description="Bin not found")
    return jsonify({
        'id': bin.id,
        'location': bin.location,
        'type': bin.type,
        'lat': bin.lat,
        'lon': bin.lon,
        'fill': bin.fill,
        'last_emptied_days_ago': bin.last_emptied_days_ago,
        'status': bin.status,
    })


@app.route('/api/collect', methods=['POST'])
def collect_bins():
    if not request.is_json:
        return jsonify({'error': 'JSON body required'}), 400
    ids = request.json.get('bin_ids')
    if not isinstance(ids, list):
        return jsonify({'error': 'bin_ids must be a list'}), 400

    collected = []
    for bin_id in ids:
        bin = Bin.query.get(bin_id)
        if bin:
            bin.fill = 0
            bin.last_emptied_days_ago = 0
            bin.status = 'ok'
            collected.append(bin_id)

    if collected:
        db.session.commit()

    return jsonify({'message': 'Bins collected and reset', 'collected_bins': collected})


@app.route("/api/optimized_route")
def optimized_route():
    bins = Bin.query.filter(Bin.status.in_(["full", "inactive"])).all()
    hub = Bin.query.get(0)
    if not bins or not hub:
        return jsonify({"path": []})

    path = [[hub.lat, hub.lon]]
    current = hub
    visited = set()

    while len(visited) < len(bins):
        nearest_bin = min(
            (b for b in bins if b.id not in visited),
            key=lambda b: calculate_distance(current, b),
            default=None
        )
        if not nearest_bin:
            break
        path.append([nearest_bin.lat, nearest_bin.lon])
        visited.add(nearest_bin.id)
        current = nearest_bin

    path.append([hub.lat, hub.lon])
    return jsonify({"path": path})


@app.route('/bin/<int:bin_id>')
def show_bin(bin_id):
    bin = Bin.query.get(bin_id)
    if not bin:
        abort(404, description="Bin not found")
    return render_template('bin_detail.html', bin=bin)


# --- Haversine Distance ---
def calculate_distance(a, b):
    R = 6371
    lat1, lon1 = radians(a.lat), radians(a.lon)
    lat2, lon2 = radians(b.lat), radians(b.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a_ = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a_), sqrt(1 - a_))
    return R * c


# --- Randomizer (Runs in Background) ---
def auto_randomize_fill():
    while True:
        with app.app_context():
            try:
                bins = Bin.query.filter(Bin.type != 'HUB').all()
                for bin in bins:
                    bin.fill = random.randint(0, 100)
                    bin.last_emptied_days_ago += random.randint(0, 1)
                db.session.commit()
            except:
                db.session.rollback()
        time.sleep(30)


# --- App Startup ---
if __name__ == '__main__':
    with app.app_context():
        init_db()
    threading.Thread(target=auto_randomize_fill, daemon=True).start()
    app.run(debug=False)
