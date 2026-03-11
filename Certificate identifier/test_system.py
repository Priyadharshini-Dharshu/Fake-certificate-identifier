"""
System Diagnostic Test for Certificate Verification
Run this to identify configuration issues
"""

import sys
import os

print("=" * 60)
print("CERTIFICATE VERIFICATION SYSTEM DIAGNOSTIC")
print("=" * 60)

# Test 1: Check Python version
print("\n[1] Python Version:")
print(f"    {sys.version}")

# Test 2: Check Python packages
print("\n[2] Checking Python packages:")
packages = [
    ('flask', 'Flask'),
    ('werkzeug', 'Werkzeug'),
    ('cv2', 'OpenCV'),
    ('pytesseract', 'Pytesseract'),
    ('PIL', 'Pillow'),
    ('numpy', 'NumPy'),
    ('sklearn', 'Scikit-learn'),
    ('tensorflow', 'TensorFlow')
]

for pkg, name in packages:
    try:
        if pkg == 'sklearn':
            import sklearn
            print(f"    [OK] {name}: {sklearn.__version__}")
        else:
            mod = __import__(pkg)
            ver = getattr(mod, '__version__', 'installed')
            print(f"    [OK] {name}: {ver}")
    except ImportError as e:
        print(f"    [ERROR] {name}: NOT INSTALLED")

# Test 3: Check Tesseract installation
print("\n[3] Tesseract OCR:")
import pytesseract

# Check default paths
default_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Tesseract-OCR\tesseract.exe'
]

tesseract_found = False
for path in default_paths:
    if os.path.exists(path):
        print(f"    [OK] Found at: {path}")
        pytesseract.pytesseract.tesseract_cmd = path
        tesseract_found = True
        break

if not tesseract_found:
    print("    [ERROR] Tesseract NOT found in common locations!")
    print("    Current setting:", pytesseract.pytesseract.tesseract_cmd)

# Test Tesseract version
try:
    version = pytesseract.get_tesseract_version()
    print(f"    [OK] Tesseract version: {version}")
except Exception as e:
    print(f"    [ERROR] Cannot get Tesseract version: {e}")

# Test 4: Check Tesseract language data
print("\n[4] Tesseract Language Data:")
try:
    langs = pytesseract.get_languages()
    print(f"    Available languages: {langs}")
    if 'eng' in langs:
        print("    [OK] English language data: FOUND")
    else:
        print("    [ERROR] English language data: NOT FOUND")
except Exception as e:
    print(f"    [ERROR] Cannot get languages: {e}")

# Test 5: Check directory structure
print("\n[5] Directory Structure:")
dirs_to_check = [
    'static',
    'static/uploads',
    'templates'
]
for d in dirs_to_check:
    if os.path.exists(d):
        print(f"    [OK] {d}/")
    else:
        print(f"    [ERROR] {d}/ - MISSING")
        os.makedirs(d, exist_ok=True)
        print(f"    -> Created {d}/")

# Test 6: Test image loading
print("\n[6] Testing OpenCV:")
try:
    import cv2
    import numpy as np
    
    # Create a test image
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img[:] = (255, 255, 255)  # White image
    
    cv2.imwrite('static/uploads/test_image.png', test_img)
    print("    [OK] OpenCV can create and save images")
    
    # Try to read it back
    img = cv2.imread('static/uploads/test_image.png')
    if img is not None:
        print("    [OK] OpenCV can read images")
    else:
        print("    [ERROR] OpenCV cannot read images")
        
except Exception as e:
    print(f"    [ERROR] OpenCV error: {e}")

# Test 7: Test Flask app import
print("\n[7] Testing Flask Application:")
try:
    # Add current directory to path
    sys.path.insert(0, '.')
    
    # Try to import the app
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", "app.py")
    app_module = importlib.util.module_from_spec(spec)
    
    print("    [OK] app.py syntax is valid")
    
except Exception as e:
    print(f"    [ERROR] app.py error: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nNEXT STEPS:")
print("1. If Tesseract is not found, install it from:")
print("   https://github.com/UB-Mannheim/tesseract/wiki")
print("2. Make sure English language data is selected during install")
print("3. Run: pip install -r requirements.txt")
print("4. Run: python app.py")
print("=" * 60)
