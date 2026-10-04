import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campusfix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default='Submitted')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "description": self.description,
            "category": self.category,
            "department": self.department,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

# Smart AI Triage Engine
def ai_triage(title, description, location):
    text = f"{title} {description} {location}".lower()
    
    # Priority Keywords
    high_priority_keywords = [
        'exam', 'test', 'urgent', 'emergency', 'leak', 'flooding', 
        'fire', 'hazard', 'power cut', 'outage', 'smoke', 'broken key', 'lockout'
    ]
    medium_priority_keywords = [
        'projector', 'wifi', 'internet', 'ac', 'air conditioner', 
        'fan', 'light', 'clean', 'trash', 'water'
    ]
    
    # Category Rules
    if any(k in text for k in ['projector', 'computer', 'lab', 'wifi', 'internet', 'screen', 'monitor', 'cable', 'hdmi']):
        category = "IT / Equipment"
        department = "IT Support"
    elif any(k in text for k in ['water', 'pipe', 'leak', 'toilet', 'tap', 'sink', 'plumbing', 'drain']):
        category = "Plumbing"
        department = "Facilities & Maintenance"
    elif any(k in text for k in ['light', 'fan', 'switch', 'socket', 'wire', 'power', 'electricity']):
        category = "Electrical"
        department = "Electrical Maintenance"
    elif any(k in text for k in ['dirty', 'dust', 'clean', 'trash', 'garbage', 'smell', 'washroom']):
        category = "Sanitation"
        department = "Housekeeping"
    else:
        category = "General Repairs"
        department = "Campus Maintenance"

    # Priority Decision Engine
    if any(k in text for k in high_priority_keywords):
        priority = "High"
    elif any(k in text for k in medium_priority_keywords):
        priority = "Medium"
    else:
        priority = "Low"
        
    return category, department, priority

# Initialize Database
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/issues', methods=['GET'])
def get_issues():
    issues = Issue.query.order_by(Issue.created_at.desc()).all()
    return jsonify([issue.to_dict() for issue in issues])

@app.route('/api/issues', methods=['POST'])
def create_issue():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    location = data.get('location', '').strip()
    description = data.get('description', '').strip()

    if not title or not location or not description:
        return jsonify({"error": "Title, location, and description are required."}), 400

    category, department, priority = ai_triage(title, description, location)

    new_issue = Issue(
        title=title,
        location=location,
        description=description,
        category=category,
        department=department,
        priority=priority,
        status='Submitted'
    )

    db.session.add(new_issue)
    db.session.commit()

    return jsonify({
        "message": "Issue submitted and triaged successfully",
        "issue": new_issue.to_dict()
    }), 201

@app.route('/api/issues/<int:issue_id>/status', methods=['PATCH'])
def update_status(issue_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    
    valid_statuses = ['Submitted', 'Assigned', 'In Progress', 'Resolved']
    if new_status not in valid_statuses:
        return jsonify({"error": "Invalid status value"}), 400

    issue = Issue.query.get_or_404(issue_id)
    issue.status = new_status
    db.session.commit()

    return jsonify({"message": "Status updated successfully", "issue": issue.to_dict()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)