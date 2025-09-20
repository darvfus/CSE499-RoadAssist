#!/usr/bin/env python3
"""
Simple test script for drowsiness detection without GUI
"""

import cv2
import time
import numpy as np
import pygame

# Initialize pygame mixer for audio
pygame.mixer.init()

def test_audio():
    """Test audio generation"""
    try:
        duration = 500  # milliseconds
        sample_rate = 22050
        frames = int(duration * sample_rate / 1000)
        
        # Create a sine wave for alarm sound
        arr = np.zeros((frames, 2))
        for i in range(frames):
            time_val = float(i) / sample_rate
            wave = 2000 * np.sin(2 * np.pi * 800 * time_val)  # 800 Hz tone
            arr[i][0] = wave
            arr[i][1] = wave
        
        # Convert to pygame sound
        sound = pygame.sndarray.make_sound(arr.astype(np.int16))
        sound.play()
        time.sleep(0.6)
        print("✅ Audio test successful")
        return True
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

def test_camera_detection():
    """Test camera and face detection"""
    print("🔍 Testing camera and face detection...")
    print("Press 'q' to quit, 's' to test sound")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot access camera")
        return False
    
    # Load Haar cascade classifiers
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    if face_cascade.empty() or eye_cascade.empty():
        print("❌ Cannot load Haar cascades")
        return False
    
    print("✅ Camera and cascades loaded successfully")
    print("Look at the camera to test detection...")
    
    frame_count = 0
    detection_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read from camera")
            break
        
        frame_count += 1
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        eyes_detected = 0
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, "Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            # Detect eyes within face
            eyes = eye_cascade.detectMultiScale(roi_gray)
            eyes_detected += len(eyes)
            
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
                cv2.putText(roi_color, "Eye", (ex, ey-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Display detection status
        status = f"Faces: {len(faces)}, Eyes: {eyes_detected}"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Drowsiness simulation
        if eyes_detected < 2:
            cv2.putText(frame, "EYES CLOSED - DROWSY!", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            detection_count += 1
        else:
            cv2.putText(frame, "Eyes Open - Alert", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            detection_count = 0
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit, 's' for sound test", (10, frame.shape[0]-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Drowsiness Detection Test", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("Testing sound...")
            test_audio()
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n📊 Test Results:")
    print(f"Total frames processed: {frame_count}")
    print(f"Detection working: {'✅ Yes' if frame_count > 0 else '❌ No'}")
    
    return True

def main():
    """Main test function"""
    print("🚗 Driver Drowsiness Detection - Test Mode")
    print("="*50)
    
    # Test audio first
    print("\n1. Testing audio generation...")
    test_audio()
    
    # Test camera detection
    print("\n2. Testing camera detection...")
    test_camera_detection()
    
    print("\n✅ Test completed!")
    print("\nIf everything worked, you can now run:")
    print("  python driverassistant_modified.py")

if __name__ == "__main__":
    main()