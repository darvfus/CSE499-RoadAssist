#!/usr/bin/env python3
"""
Test script to verify all required packages are working correctly
"""

def test_opencv():
    """Test OpenCV installation"""
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
        
        # Test camera access
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera access: OK")
            cap.release()
        else:
            print("❌ Camera access: Failed")
        
        # Test Haar cascades
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if not face_cascade.empty() and not eye_cascade.empty():
            print("✅ Haar cascades: Loaded successfully")
        else:
            print("❌ Haar cascades: Failed to load")
            
        return True
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
        return False

def test_numpy():
    """Test NumPy installation"""
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
        
        # Test basic operations
        arr = np.array([1, 2, 3, 4, 5])
        result = np.mean(arr)
        print(f"✅ NumPy operations: Working (mean of [1,2,3,4,5] = {result})")
        return True
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False

def test_pygame():
    """Test Pygame installation"""
    try:
        import pygame
        print(f"✅ Pygame version: {pygame.version.ver}")
        
        # Test mixer initialization
        pygame.mixer.init()
        print("✅ Pygame mixer: Initialized successfully")
        
        # Test sound generation
        import numpy as np
        duration = 100  # milliseconds
        sample_rate = 22050
        frames = int(duration * sample_rate / 1000)
        
        arr = np.zeros((frames, 2))
        for i in range(frames):
            time_val = float(i) / sample_rate
            wave = 1000 * np.sin(2 * np.pi * 440 * time_val)  # 440 Hz tone
            arr[i][0] = wave
            arr[i][1] = wave
        
        sound = pygame.sndarray.make_sound(arr.astype(np.int16))
        print("✅ Pygame sound generation: Working")
        
        pygame.mixer.quit()
        return True
    except ImportError as e:
        print(f"❌ Pygame: {e}")
        return False

def test_flask():
    """Test Flask installation"""
    try:
        import flask
        print(f"✅ Flask version: {flask.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Flask: {e}")
        return False

def test_requests():
    """Test Requests installation"""
    try:
        import requests
        print(f"✅ Requests version: {requests.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Requests: {e}")
        return False

def test_tkinter():
    """Test Tkinter (should be built-in)"""
    try:
        import tkinter as tk
        print("✅ Tkinter: Available")
        return True
    except ImportError as e:
        print(f"❌ Tkinter: {e}")
        return False

def test_email():
    """Test email libraries"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        print("✅ Email libraries: Available")
        return True
    except ImportError as e:
        print(f"❌ Email libraries: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing package installations...\n")
    
    tests = [
        ("OpenCV", test_opencv),
        ("NumPy", test_numpy),
        ("Pygame", test_pygame),
        ("Flask", test_flask),
        ("Requests", test_requests),
        ("Tkinter", test_tkinter),
        ("Email", test_email)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name}: Unexpected error - {e}")
            results.append((name, False))
    
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:15} {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All packages are working correctly!")
        print("You can now run the modified driver assistant.")
    else:
        print(f"\n⚠️  {len(results) - passed} package(s) need attention.")

if __name__ == "__main__":
    main()