import streamlit as st
import cv2
import face_recognition
import numpy as np
import mysql.connector
import os
import time

# ============ MySQL Connection ============ 
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="logan",  # Update with your MySQL password
    database="attendancereg"
)
cursor = conn.cursor()

# ============ Create Database and Tables if Not Exist ============

# Create the database if it doesn't exist
cursor.execute("CREATE DATABASE IF NOT EXISTS attendancereg;")

# Use the database
cursor.execute("USE attendancereg;")

# Create the students table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        reg_no VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    );
""")

# Create the attendance table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        reg_no VARCHAR(255),
        name VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (reg_no, timestamp)
    );
""")

# ============ Load Known Faces from Folder ============ 
known_face_encodings = []
known_face_names = []

IMAGE_FOLDER = "C:/Users/sivab/OneDrive/Desktop/your_project/student_images"

# Create the folder if it doesn't exist
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)
    st.warning(f"📁 Folder '{IMAGE_FOLDER}' was missing, so it has been created.")
    st.info("🖼️ Please add student images (named with reg_no, e.g., 5084.jpg) and restart the app.")
    st.stop()

# Load student images dynamically
students = {}
for filename in os.listdir(IMAGE_FOLDER):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        reg_no = os.path.splitext(filename)[0]
        img_path = os.path.join(IMAGE_FOLDER, filename)
        students[reg_no] = img_path

# Process images
for reg_no, img_path in students.items():
    image = cv2.imread(img_path)
    if image is None:
        st.warning(f"❌ Could not load image: {img_path}")
        continue

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_image)

    if not face_locations:
        st.warning(f"❌ No face detected in image: {img_path}")
        continue

    face_encoding = face_recognition.face_encodings(rgb_image, face_locations)[0]
    known_face_encodings.append(face_encoding)
    known_face_names.append(reg_no)

# ============ Streamlit UI ============ 
st.title("📸 Face Attendance System")

# New Student Registration Section
st.header("🔐 New Student Registration")
student_id = st.text_input("Enter Student ID (e.g., 5081):")

register_button = st.button("Register New Face")

if register_button:
    if not student_id:
        st.warning("Please enter a valid Student ID to register.")
    else:
        st.warning(f"🎥 Starting webcam to register face for Student ID: {student_id}...")

        cap = cv2.VideoCapture(0)
        time.sleep(2)
        frame_window = st.image([])

        face_encodings = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Could not access webcam.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings_frame = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings_frame):
                # Store the first detected face for registration
                face_encodings.append(face_encoding)

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, f"Student ID: {student_id}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            frame_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            if len(face_encodings) > 0:
                # Save face encoding for future recognition
                known_face_encodings.append(face_encodings[0])
                known_face_names.append(student_id)

                # Save the image to the student_images folder
                student_image_path = os.path.join(IMAGE_FOLDER, f"{student_id}.jpg")
                cv2.imwrite(student_image_path, frame)  # Save the captured frame as an image

                # Save the registration details to the database
                cursor.execute("INSERT INTO students (reg_no, name) VALUES (%s, %s)", (student_id, f"Student {student_id} - Registered"))
                conn.commit()

                st.success(f"✅ Student ID {student_id} registered successfully!")
                break

        cap.release()

# Face Recognition Section
start_camera = st.button("Start Face Recognition")

if start_camera:
    st.warning("🎥 Starting webcam. Please look at the camera...")

    cap = cv2.VideoCapture(0)
    time.sleep(2)
    marked = False
    frame_window = st.image([])

    while cap.isOpened() and not marked:
        ret, frame = cap.read()
        if not ret:
            st.error("❌ Could not access webcam.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                matched_idx = matches.index(True)
                name = known_face_names[matched_idx]

                # Check if already marked today
                cursor.execute("SELECT * FROM attendance WHERE reg_no=%s AND DATE(timestamp)=CURDATE()", (name,))
                if cursor.fetchone():
                    st.info(f"ℹ️ Attendance already marked today for {name}.")
                else:
                    cursor.execute("INSERT INTO attendance (reg_no, name) VALUES (%s, %s)", (name, f"Student {name} - Present"))
                    conn.commit()
                    st.success(f"✅ Marked {name} as Present")
                marked = True
                break

            # Optional: Draw box for unrecognized face
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 2)

        frame_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cap.release()
