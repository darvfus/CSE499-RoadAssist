# CSE499-RoadAssist

## Overview

This project provides a road assistance system designed to enhance driver safety and awareness. It integrates various functionalities such as real-time monitoring of vital signs, drowsiness detection, and timely alerts to prevent accidents.

## Features

*   **Real-time Vital Signs Monitoring:** Continuously monitors the driver's vital signs to detect any anomalies or health issues.
*   **Drowsiness Detection:** Utilizes facial analysis and eye aspect ratio (EAR) calculation to detect driver drowsiness and fatigue.
*   **Alert System:** Provides timely audio and visual alerts to the driver in case of drowsiness or critical vital sign changes.
*   **Email Notifications:** Sends email notifications to designated contacts in case of emergencies or critical situations.
*   **User Management:** Allows registration and management of user profiles, including personal information and emergency contacts.
*   **Data Analysis and Visualization:** Provides tools for analyzing and visualizing collected data, such as vital signs and drowsiness patterns.

## Technologies Used

*   **Python:** The primary programming language used for developing the road assistance system.
*   **SQLite:** Used for storing user data and other application-related information.
*   **OpenCV:** Used for facial analysis and drowsiness detection.
*   **SciPy:** Used for signal processing and data analysis.
*   **Tkinter:** Used for creating the graphical user interface (GUI).
*   **PyAudio:** Used for playing audio alerts.
*   **smtplib:** Used for sending email notifications.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/RoadAssist.git
    cd RoadAssist
    ```
2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```
3.  **Database setup:**

    *   Create a database file (e.g., `usuarios.db`) using SQLite.
    *   Run the `db.py` script to create the necessary tables:

        ```bash
        python db.py
        ```
4.  **Configuration:**

    *   Update the `users.json` file with user information.
    *   Configure email settings in the `email_service` module.

## Usage

1.  **Run the main script:**

    ```bash
    python main.py
    ```
2.  **Register a user:**

    *   Use the registration interface to create a new user profile.
3.  **Start the program:**

    *   Use the program interface to start the road assistance system.
4.  **Monitor the driver:**

    *   The system will continuously monitor the driver's vital signs and drowsiness levels.
5.  **Receive alerts:**

    *   The system will provide audio and visual alerts in case of drowsiness or critical vital sign changes.

## Modules

*   **db.py:** Contains functions for database operations, such as creating a table, adding users, searching for users, and listing users.
*   **driverassitan2.py:** Contains functions related to driver assistance, including loading and saving user data, playing audio, getting vital signs, sending emails, calculating EAR (Eye Aspect Ratio), calculating BMI, classifying BMI, calculating metabolic age, starting detection, showing graphs, and GUI functions for registration.
*   **driverassitant.py:** Similar to driverassitan2.py, but potentially an older version or with slightly different functionalities. Contains functions for playing audio, getting vital signs, sending emails, calculating EAR, and starting detection.
*   **interfaz.py:** Contains functions for the user interface, such as starting the program, stopping the program, and registering a user.
*   **main.py:** The main entry point of the program. Contains functions for loading and saving users, playing audio, getting vital signs, sending emails, calculating EAR, starting detection, and GUI functions for registration and program control.
*   **email\_service/:** Directory containing modules for sending emails.

## Team

Daniel Romero
Nyasha Ushewokunze
Sarah Imarhenakhue Ogiefa
