import tkinter as tk
from tkinter import messagebox
import threading
import cv2
import time
import mediapipe as mp
import numpy as np
import json
import os
from playsound import playsound
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import mailtrap as mt

# =============================
# CONFIGURACIÓN
# =============================
USERS_FILE = "users.json"
EAR_THRESHOLD = 0.2
SLEEP_THRESHOLD_TIME = 3

# =============================
# GESTIÓN DE USUARIOS
# =============================
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users = load_users()
sleep_events = []  # historial de eventos de sueño

# =============================
# FUNCIONES AUXILIARES
# =============================
def play_audio(audio_path):
    try:
        playsound(audio_path)
    except Exception as e:
        print(f"Error playing audio: {e}")

def get_vital_signs():
    heart_rate = np.random.randint(60, 100)
    respiration = np.random.randint(12, 20)
    blood_pressure = f"{np.random.randint(110, 120)}/{np.random.randint(70, 80)}"
    temperature = round(np.random.uniform(36.5, 37.5), 1)
    return heart_rate, respiration, blood_pressure, temperature

def send_email(user_name, user_email):
    """Envía correo con Mailtrap cuando el usuario se duerme"""
    heart_rate, respiration, bp, temp = get_vital_signs()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    subject = f"Sleep Alert - {user_name}"
    body = f"""
    ALERTA DE SOMNOLENCIA

    Usuario: {user_name}
    Hora detectada: {timestamp}

    Signos vitales:
    ❤️ Heart rate: {heart_rate} BPM
    🌬️ Respiration rate: {respiration} breaths/min
    💉 Blood pressure: {bp} mmHg
    🌡️ Body temperature: {temp} °C

    El sistema ha detectado que el usuario se durmió durante la sesión.
    """

    try:
        mail = mt.Mail(
            sender=mt.Address(email="hello@demomailtrap.co", name="Sleep Detection System"),
            to=[mt.Address(email=user_email)],
            subject=subject,
            text=body,
            category="Sleep Alert"
        )

        client = mt.MailtrapClient(token="09dac62be08176ae806cae2291cda74e")
        response = client.send(mail)
        print("✅ Email enviado correctamente:", response)
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

def calculate_EAR(points):
    A = np.linalg.norm(points[1] - points[5])
    B = np.linalg.norm(points[2] - points[4])
    C = np.linalg.norm(points[0] - points[3])
    return (A + B) / (2.0 * C)

# =============================
# CÁLCULOS
# =============================
def calculate_bmi(weight, height):
    return weight / (height ** 2)

def classify_bmi(bmi):
    if bmi < 18.5:
        return "Low (Risk)"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Danger (Obesity)"

def calculate_metabolic_age(age, bmi, gender):
    adjustment = 0
    if gender.lower() == "male":
        adjustment = 2
    elif gender.lower() == "female":
        adjustment = -2
    return age + int((bmi - 22)) + adjustment

# =============================
# DETECCIÓN DE SUEÑO
# =============================
stop_flag = False
reset_flag = False

def start_detection(user_name, user_email):
    global stop_flag, reset_flag, sleep_events
    cap = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    eyes_closed_start = None

    while cap.isOpened():
        if stop_flag:
            break

        if reset_flag:
            reset_flag = False
            eyes_closed_start = None

        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(frame_rgb)
        h, w, _ = frame.shape

        if result.multi_face_landmarks:
            for face in result.multi_face_landmarks:
                right_eye_points = [(int(face.landmark[idx].x * w), int(face.landmark[idx].y * h)) for idx in [33, 160, 158, 133, 153, 144]]
                EAR_right = calculate_EAR(np.array(right_eye_points))

                left_eye_points = [(int(face.landmark[idx].x * w), int(face.landmark[idx].y * h)) for idx in [362, 385, 387, 263, 373, 380]]
                EAR_left = calculate_EAR(np.array(left_eye_points))

                EAR = (EAR_right + EAR_left) / 2.0

                if EAR < EAR_THRESHOLD:
                    cv2.putText(frame, "Eyes Closed", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    if eyes_closed_start is None:
                        eyes_closed_start = time.time()
                    elif time.time() - eyes_closed_start >= SLEEP_THRESHOLD_TIME:
                        play_audio(r"C:\Users\Daniel Romero\Desktop\neural\alarma.mp3")
                        send_email(user_name, user_email)
                        event = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - User asleep"
                        sleep_events.append(event)
                        eyes_closed_start = None
                else:
                    eyes_closed_start = None
                    cv2.putText(frame, "Eyes Open", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Eye Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# =============================
# GRÁFICA DE SIGNOS VITALES
# =============================
def show_graph():
    plt.ion()
    fig, axs = plt.subplots(2, 2, figsize=(8, 6))
    plt.subplots_adjust(hspace=0.5)

    x_data, hr_data, resp_data, temp_data, bp_data = [], [], [], [], []

    def animate(i):
        t = len(x_data)
        x_data.append(t)
        hr, resp, bp, temp = get_vital_signs()
        hr_data.append(hr)
        resp_data.append(resp)
        bp_data.append(int(bp.split("/")[0]))
        temp_data.append(temp)

        axs[0,0].cla(); axs[0,0].plot(x_data, hr_data, "r-"); axs[0,0].set_title("Heart Rate")
        axs[0,1].cla(); axs[0,1].plot(x_data, resp_data, "g-"); axs[0,1].set_title("Respiration")
        axs[1,0].cla(); axs[1,0].plot(x_data, bp_data, "b-"); axs[1,0].set_title("Systolic Pressure")
        axs[1,1].cla(); axs[1,1].plot(x_data, temp_data, "m-"); axs[1,1].set_title("Temperature")

    ani = FuncAnimation(fig, animate, interval=3000)
    plt.show(block=False)

    while not stop_flag:
        plt.pause(1)
    plt.close(fig)

# =============================
# INTERFAZ GRÁFICA
# =============================
def register_window():
    def register():
        name = entry_name.get()
        email = entry_email.get()
        try:
            age = int(entry_age.get())
            height = float(entry_height.get()) / 100
            weight = float(entry_weight.get())
        except ValueError:
            messagebox.showerror("Error", "Age, height, and weight must be numeric.")
            return
        gender = entry_gender.get()

        if not name or not email or not gender:
            messagebox.showwarning("Error", "Please complete all fields.")
            return

        users[name] = {"email": email, "age": age, "gender": gender, "height": height, "weight": weight}
        save_users(users)
        messagebox.showinfo("Registration", "User successfully registered.")
        reg.destroy()

    reg = tk.Toplevel(bg="#e8f0fe")
    reg.title("User Registration")
    reg.geometry("300x350")

    tk.Label(reg, text="User Registration", font=("Arial", 14, "bold"), bg="#e8f0fe").pack(pady=10)
    tk.Label(reg, text="Name:", bg="#e8f0fe").pack()
    entry_name = tk.Entry(reg); entry_name.pack()
    tk.Label(reg, text="Email:", bg="#e8f0fe").pack()
    entry_email = tk.Entry(reg); entry_email.pack()
    tk.Label(reg, text="Age:", bg="#e8f0fe").pack()
    entry_age = tk.Entry(reg); entry_age.pack()
    tk.Label(reg, text="Gender (Male/Female):", bg="#e8f0fe").pack()
    entry_gender = tk.Entry(reg); entry_gender.pack()
    tk.Label(reg, text="Height (cm):", bg="#e8f0fe").pack()
    entry_height = tk.Entry(reg); entry_height.pack()
    tk.Label(reg, text="Weight (kg):", bg="#e8f0fe").pack()
    entry_weight = tk.Entry(reg); entry_weight.pack()
    tk.Button(reg, text="Register", bg="#4CAF50", fg="white", command=register).pack(pady=10)

def start():
    global stop_flag, reset_flag
    name = entry_user.get()
    if name not in users:
        messagebox.showerror("Error", "User not registered.")
        return

    play_audio(r"C:\Users\Daniel Romero\Desktop\neural\harry.mp3")
    threading.Thread(target=show_graph, daemon=True).start()
    email = users[name]["email"]
    stop_flag = False
    threading.Thread(target=start_detection, args=(name, email), daemon=True).start()

def stop():
    global stop_flag
    stop_flag = True

def reset_btn():
    global reset_flag
    reset_flag = True

def exit_and_save():
    global stop_flag, sleep_events
    stop_flag = True
    name = entry_user.get()
    if name not in users:
        root.destroy()
        return

    data = users[name]
    bmi = calculate_bmi(data["weight"], data["height"])
    classification = classify_bmi(bmi)
    metabolic_age = calculate_metabolic_age(data["age"], bmi, data["gender"])

    report = f"""
User Report - {name}
Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Age: {data['age']} years
Gender: {data['gender']}
Height: {data['height']:.2f} m
Weight: {data['weight']} kg

BMI: {bmi:.2f}
Classification: {classification}

Estimated Metabolic Age: {metabolic_age} years

Sleep Events History:
"""
    for event in sleep_events:
        report += f"{event}\n"

    with open("user_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    messagebox.showinfo("Exit", "Data saved to 'user_report.txt'")
    root.destroy()

# =============================
# VENTANA PRINCIPAL
# =============================
root = tk.Tk()
root.title("Sleep Detection System")
root.geometry("350x400")
root.configure(bg="#e8f0fe")

tk.Label(root, text="Sleep Detection System", font=("Arial", 16, "bold"), bg="#e8f0fe", fg="#1a73e8").pack(pady=15)

tk.Button(root, text="Register User", command=register_window, bg="#34a853", fg="white", font=("Arial", 12, "bold"), width=20).pack(pady=10)

tk.Label(root, text="User Name:", bg="#e8f0fe", font=("Arial", 12)).pack(pady=5)
entry_user = tk.Entry(root, font=("Arial", 12))
entry_user.pack()

tk.Button(root, text="Start Session", bg="#1a73e8", fg="white", font=("Arial", 12, "bold"), command=start, width=20).pack(pady=5)
tk.Button(root, text="Stop", bg="#ea4335", fg="white", font=("Arial", 12, "bold"), command=stop, width=20).pack(pady=5)
tk.Button(root, text="Reset", bg="#fbbc05", fg="black", font=("Arial", 12, "bold"), command=reset_btn, width=20).pack(pady=5)
tk.Button(root, text="Exit & Save Report", bg="black", fg="white", font=("Arial", 12, "bold"), command=exit_and_save, width=20).pack(pady=15)

root.mainloop()
