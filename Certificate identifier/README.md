# Certificate Authenticity Verification System

AI-powered certificate verification system using Tesseract OCR and machine learning to detect fake certificates.

## Features

- **Tesseract OCR Integration**: Extracts text from certificate images
- **AI Analysis**: Uses multiple features to determine authenticity
- **Image Preprocessing**: Advanced image enhancement for better OCR
- **Modern UI**: Bootstrap-based responsive interface
- **Real-time Results**: Instant certificate verification

## Prerequisites

- Python 3.10.11
- Tesseract OCR (download from: https://github.com/UB-Mannheim/tesseract/wiki)

## Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Tesseract OCR**:
   - Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install it to the default location: `C:\Program Files\Tesseract-OCR\`
   - Make sure to select the English language data during installation

3. **Update Tesseract path** (if different):
   - Open `app.py`
   - Update this line with your Tesseract path:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

## Running the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## How It Works

### 1. Image Upload
- User uploads a certificate image (PNG, JPG, JPEG, GIF, BMP, WEBP)
- Preview is displayed

### 2. OCR Processing
- Tesseract extracts text from the certificate
- Image preprocessing (contrast enhancement, denoising, thresholding)

### 3. Feature Extraction
The system analyzes:
- **Image Sharpness**: Using Laplacian variance
- **Text Density**: Amount of text relative to image size
- **Keyword Detection**: Checks for certificate-specific keywords
- **Image Entropy**: Measures information content
- **Contrast & Brightness**: Image quality metrics
- **Suspicious Regions**: Detects uniform areas (possible copy-paste)
- **Edge Analysis**: Checks for signs of tampering

### 4. AI Prediction
- Rule-based scoring system analyzes all features
- Returns authenticity verdict with confidence score

## Verification Results

| Result | Description |
|--------|-------------|
| ✅ Authentic | High confidence certificate is real |
| ✅ Likely Authentic | Certificate appears genuine |
| ⚠ Suspicious | Some concerns detected |
| ❌ Fake | High confidence certificate is fake |

## Project Structure

```
Certificate identifier/
├── app.py                 # Flask backend with OCR & AI
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Bootstrap frontend
├── static/
│   └── uploads/          # Uploaded certificates
└── README.md             # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main page |
| `/verify` | POST | Verify certificate |
| `/api/health` | GET | Health check |

## Troubleshooting

### Tesseract not found
- Make sure Tesseract is installed
- Update the path in `app.py` to match your installation

### OCR returns empty text
- Ensure image is clear and not blurry
- Try images with good contrast
- Make sure the certificate contains text

### Import errors
- Reinstall requirements: `pip install -r requirements.txt`

## License

This project is for educational purposes.
