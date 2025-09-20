# Driver Drowsiness Detection System - Modified Version

This is a modified version of the original driver assistant that works with the available packages on your system.

## Changes Made

### ✅ What Works Now:
- **Face Detection**: Uses OpenCV's Haar Cascades instead of MediaPipe
- **Audio Alerts**: Uses Pygame instead of playsound
- **Eye Detection**: Simplified detection using OpenCV built-in classifiers
- **Email Alerts**: Still functional with vital signs simulation
- **GUI**: Same Tkinter interface

### ❌ What Was Removed/Changed:
- **MediaPipe**: Replaced with OpenCV Haar cascades (less accurate but functional)
- **Playsound**: Replaced with Pygame audio generation
- **Complex EAR calculation**: Simplified for basic eye detection

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Test your installation:
```bash
python test_packages.py
```

## Usage

### Option 1: Run the Modified Version
```bash
python driverassistant_modified.py
```

### Option 2: Test Packages First
```bash
python test_packages.py
```

## Configuration

1. **Email Setup**: Edit the email credentials in `driverassistant_modified.py`:
   ```python
   SENDER_EMAIL = "your_email@gmail.com"
   PASSWORD = "your_app_password"  # Use Gmail App Password
   ```

2. **Detection Parameters**: Adjust these values if needed:
   ```python
   umbral_EAR = 0.25  # Eye closure threshold
   umbral_tiempo_dormido = 3  # Seconds before alarm
   ```

## How It Works

1. **Face Detection**: Uses OpenCV's Haar cascade to detect faces
2. **Eye Detection**: Detects eyes within detected faces
3. **Drowsiness Logic**: If fewer than 2 eyes are detected for 3+ seconds, triggers alarm
4. **Alerts**: Plays audio beep and sends email notification

## Limitations

- **Less Accurate**: Haar cascades are less precise than MediaPipe
- **Lighting Sensitive**: Requires good lighting conditions
- **Simple Detection**: Basic eye open/closed detection vs. advanced EAR calculation
- **False Positives**: May trigger if you look away or blink frequently

## Troubleshooting

### Camera Issues:
- Make sure no other applications are using the camera
- Try different camera indices (0, 1, 2) in `cv2.VideoCapture()`

### Audio Issues:
- The system will fallback to Windows system beep if Pygame fails
- Check that your speakers/headphones are working

### Email Issues:
- Use Gmail App Passwords instead of regular passwords
- Enable 2-factor authentication on Gmail
- Check firewall settings

## Future Improvements

To get better accuracy, consider:
1. Installing MediaPipe manually for your Python version
2. Using dlib for better facial landmark detection
3. Implementing more sophisticated eye tracking algorithms
4. Adding calibration for different users

## Files

- `driverassistant_modified.py` - Main modified application
- `test_packages.py` - Package testing script
- `requirements.txt` - Updated package list
- `README_MODIFIED.md` - This documentation