"""
Certificate Authenticity Verification System
Uses Tesseract OCR and AI to detect fake certificates
"""

import os
import cv2
import numpy as np
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import pickle
from datetime import datetime
from functools import wraps

# Configure Tesseract path (update this to your Tesseract installation)
# On Windows, it might be: C:\Program Files\Tesseract-OCR\tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'certverify-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_users():
    """Load users from JSON file"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                return json.load(f)
        return []
    except:
        return []

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load AI model (we'll create a simple one for demonstration)
MODEL_PATH = 'certificate_model.pkl'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply image preprocessing
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        # Threshold
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extract text
        text = pytesseract.image_to_string(thresh, lang='eng')
        
        return text, True
    except Exception as e:
        return str(e), False

def analyze_certificate_features(image_path, extracted_text):
    """Extract features from certificate for AI analysis"""
    features = {}
    
    try:
        # Read image
        img = cv2.imread(image_path)
        height, width = img.shape[:2]
        
        # Feature 1: Image dimensions ratio
        features['aspect_ratio'] = width / height if height > 0 else 0
        
        # Feature 2: Calculate image sharpness (Laplacian variance)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        features['sharpness'] = laplacian.var()
        
        # Feature 3: Text density in extracted text
        text_length = len(extracted_text.replace('\n', '').replace(' ', ''))
        features['text_density'] = text_length / (width * height / 1000)
        
        # Feature 4: Number of text blocks
        features['text_blocks'] = len([x for x in extracted_text.split('\n') if x.strip()])
        
        # Feature 5: Presence of common certificate keywords
        keywords = ['certificate', 'certify', 'awarded', 'this is to', 'successfully', 
                   'completion', 'date', 'signature', 'seal', 'stamp']
        text_lower = extracted_text.lower()
        features['keyword_count'] = sum(1 for kw in keywords if kw in text_lower)
        
        # Feature 6: Image quality metrics
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        
        # Entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        features['entropy'] = entropy
        
        # Feature 7: Check for signs of tampering (edge analysis)
        edges = cv2.Canny(gray, 50, 150)
        features['edge_density'] = np.sum(edges > 0) / edges.size
        
        # Feature 8: Average brightness
        features['brightness'] = np.mean(gray)
        
        # Feature 9: Contrast
        features['contrast'] = np.std(gray)
        
        # Feature 10: Check for uniform regions (possible copy-paste)
        features['uniform_regions'] = detect_uniform_regions(gray)
        
    except Exception as e:
        print(f"Error analyzing features: {e}")
        features = {
            'aspect_ratio': 1.4,
            'sharpness': 100,
            'text_density': 0.1,
            'text_blocks': 10,
            'keyword_count': 3,
            'entropy': 5,
            'edge_density': 0.1,
            'brightness': 128,
            'contrast': 50,
            'uniform_regions': 0
        }
    
    return features

def detect_uniform_regions(gray):
    """Detect potentially suspicious uniform regions"""
    # Divide image into grid
    h, w = gray.shape
    grid_size = 50
    uniform_count = 0
    
    for i in range(0, h - grid_size, grid_size):
        for j in range(0, w - grid_size, grid_size):
            region = gray[i:i+grid_size, j:j+grid_size]
            std = np.std(region)
            if std < 5:  # Very low variation
                uniform_count += 1
    
    return uniform_count

def predict_authenticity(features, extracted_text):
    """Predict if certificate is REAL or FAKE using AI"""
    # Simple rule-based AI with weighted features
    # In production, you would use a trained ML model
    
    score = 0
    max_score = 100
    reasons = []
    
    # Check if the image actually contains certificate-like content
    # If no certificate keywords found, it's likely not a certificate
    keywords = ['certificate', 'certify', 'awarded', 'this is to', 'successfully', 
               'completion', 'date', 'signature', 'seal', 'stamp', 'diploma', 'degree',
               'issued', 'name', 'course', 'training', 'participant', 'achievement',
               'award', 'present', 'recognition', 'qualification']
    text_lower = extracted_text.lower()
    keyword_count = sum(1 for kw in keywords if kw in text_lower)
    
    # CRITICAL: If no certificate keywords found, classify as FAKE immediately
    if keyword_count == 0:
        return {
            'result': 'FAKE',
            'confidence': 95,
            'score': -50,
            'real_percentage': 0,
            'reasons': ['No certificate-related keywords found in the image', 
                       'This does not appear to be a certificate'],
            'passing_percentage': 0
        }
    
    # CRITICAL: If very few keywords, likely not a certificate
    if keyword_count < 2:
        score -= 30
        reasons.append('Very few certificate keywords detected')
    
    # Check if text blocks are sufficient (certificates have multiple text sections)
    text_blocks = len([x for x in extracted_text.split('\n') if x.strip()])
    if text_blocks < 5:
        score -= 20
        reasons.append('Insufficient text content for a certificate')
    
    # Weight each feature
    if features.get('sharpness', 0) > 50:
        score += 15
    else:
        score -= 10
        reasons.append('Low image sharpness')
    
    if features.get('text_density', 0) > 0.05:
        score += 15
    else:
        score -= 10
        reasons.append('Low text density')
    
    if keyword_count >= 3:
        score += 20
    else:
        score -= 15
        reasons.append('Missing certificate keywords')
    
    if features.get('entropy', 0) > 4:
        score += 15
    else:
        score -= 10
        reasons.append('Low image entropy')
    
    if features.get('contrast', 0) > 30:
        score += 10
    else:
        reasons.append('Low contrast')
    
    if 0.7 < features.get('aspect_ratio', 1.4) < 1.5:
        score += 10
    else:
        reasons.append('Unusual aspect ratio')
    
    if features.get('edge_density', 0) > 0.05:
        score += 10
    else:
        score -= 5
        reasons.append('Low edge density')
    
    # Uniform regions indicate possible tampering
    if features.get('uniform_regions', 0) > 20:
        score -= 15
        reasons.append('Suspicious uniform regions detected')
    
    # Calculate real percentage (confidence that certificate is real)
    # Score ranges from negative (fake indicators) to positive (real indicators)
    # Normalize to 0-100% scale where 0% = definitely fake, 100% = definitely real
    real_percentage = ((score + 100) / 200) * 100
    real_percentage = max(0, min(100, real_percentage))  # Clamp to 0-100
    
    # Calculate confidence based on how far from neutral
    confidence = abs(score) / max_score * 100
    
    # If real percentage >= 40%, classify as REAL
    # Otherwise classify as FAKE
    if real_percentage >= 40:
        return {
            'result': 'REAL',
            'confidence': min(confidence, 95),
            'score': score,
            'real_percentage': real_percentage,
            'reasons': reasons if reasons else ['Certificate passed verification checks'],
            'passing_percentage': real_percentage
        }
    else:
        return {
            'result': 'FAKE',
            'confidence': min(confidence, 95),
            'score': score,
            'real_percentage': real_percentage,
            'reasons': reasons if reasons else ['Certificate shows fake indicators'],
            'passing_percentage': real_percentage
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['admin_id'] = user['id']
                session['admin_username'] = user['username']
                session['admin_role'] = user['role']
                flash('Login successful!', 'success')
                return redirect(url_for('admin'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('admin_role', None)
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('admin_login'))

def save_verification_report(data):
    """Save verification report to JSON file"""
    try:
        # Load existing reports
        if os.path.exists('reports.json'):
            with open('reports.json', 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        # Add new report
        reports.append(data)
        
        # Keep only last 100 reports
        reports = reports[-100:]
        
        # Save back
        with open('reports.json', 'w') as f:
            json.dump(reports, f, indent=2)
    except Exception as e:
        print(f"Error saving report: {e}")

@app.route('/verify', methods=['POST'])
def verify_certificate():
    """Handle certificate verification request"""
    if 'certificate' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['certificate']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text using Tesseract
        extracted_text, ocr_success = extract_text_from_image(filepath)
        
        if not ocr_success:
            return jsonify({
                'error': f'OCR failed: {extracted_text}',
                'filename': filename
            }), 500
        
        # Analyze features
        features = analyze_certificate_features(filepath, extracted_text)
        
        # Get AI prediction (pass extracted text to check for certificate keywords)
        prediction = predict_authenticity(features, extracted_text)
        
        # Create report data
        report_data = {
            'id': len(json.load(open('reports.json'))) + 1 if os.path.exists('reports.json') else 1,
            'filename': filename,
            'certificate_name': os.path.splitext(file.filename)[0] if file.filename else 'Unknown',
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': prediction['result'],
            'confidence': float(prediction['confidence']),
            'real_percentage': float(round(prediction.get('real_percentage', 0), 2)),
            'passing_percentage': float(round(prediction.get('passing_percentage', 0), 2)),
            'reasons': prediction.get('reasons', []),
            'extracted_text': extracted_text[:200] + '...' if len(extracted_text) > 200 else extracted_text,
            'features': {
                'sharpness': float(round(float(features.get('sharpness', 0)), 2)),
                'text_density': float(round(float(features.get('text_density', 0)), 4)),
                'keyword_count': int(features.get('keyword_count', 0)),
                'entropy': float(round(float(features.get('entropy', 0)), 2)),
                'contrast': float(round(float(features.get('contrast', 0)), 2)),
                'uniform_regions': int(features.get('uniform_regions', 0))
            }
        }
        
        # Save the report
        save_verification_report(report_data)
        
        # Return results - convert numpy types to Python native types
        return jsonify({
            'success': True,
            'filename': filename,
            'extracted_text': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
            'features': {
                'sharpness': float(round(float(features.get('sharpness', 0)), 2)),
                'text_density': float(round(float(features.get('text_density', 0)), 4)),
                'keyword_count': int(features.get('keyword_count', 0)),
                'entropy': float(round(float(features.get('entropy', 0)), 2)),
                'contrast': float(round(float(features.get('contrast', 0)), 2)),
                'uniform_regions': int(features.get('uniform_regions', 0))
            },
            'prediction': {
                'result': str(prediction['result']),
                'confidence': float(prediction['confidence']),
                'score': int(prediction['score']),
                'real_percentage': float(round(prediction.get('real_percentage', 0), 2)),
                'passing_percentage': float(round(prediction.get('passing_percentage', 0), 2)),
                'reasons': prediction.get('reasons', [])
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
@login_required
def get_reports():
    """Get all verification reports"""
    try:
        if os.path.exists('reports.json'):
            with open('reports.json', 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        # Calculate statistics - now only REAL and FAKE
        total = len(reports)
        real = len([r for r in reports if r.get('status') == 'REAL'])
        fake = len([r for r in reports if r.get('status') == 'FAKE'])
        
        return jsonify({
            'success': True,
            'reports': reports,
            'statistics': {
                'total': total,
                'real': real,
                'fake': fake
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['DELETE'])
@login_required
def clear_reports():
    """Clear all reports"""
    try:
        with open('reports.json', 'w') as f:
            json.dump([], f)
        return jsonify({'success': True, 'message': 'All reports cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """Delete a specific report"""
    try:
        if os.path.exists('reports.json'):
            with open('reports.json', 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports = [r for r in reports if r.get('id') != report_id]
        
        with open('reports.json', 'w') as f:
            json.dump(reports, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Report deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user', methods=['GET'])
def get_current_user():
    """Get current logged in user info"""
    if 'admin_id' in session:
        return jsonify({
            'logged_in': True,
            'username': session.get('admin_username'),
            'role': session.get('admin_role')
        })
    return jsonify({'logged_in': False})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if the API is running"""
    return jsonify({
        'status': 'running',
        'tesseract': 'configured',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
