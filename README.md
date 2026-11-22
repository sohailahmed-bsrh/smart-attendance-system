<div align="center">

<h1>Smart Biometric Attendance Verification System</h1>

<img src="https://readme-typing-svg.herokuapp.com?font=Inter&weight=800&size=22&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&width=800&lines=Facial+Biometric+Verification+Engine;Real-Time+Landmark+Tracking;Automated+Logging+%26+Excel+Reporting;Desktop+GUI+%2B+Web+Management+Console" alt="Typing Header" />

<p><strong>Real-Time Facial Recognition Attendance Management System with Anti-Spoofing Architecture</strong></p>

<p>
  <a href="https://skillicons.dev"><img src="https://skillicons.dev/icons?i=python,opencv,flask,github&theme=dark" alt="Skills" /></a>
</p>

</div>

---

## Executive Summary

The Smart Biometric Attendance Verification System replaces manual record-keeping with automated computer vision authentication. Utilizing 128-dimensional facial embedding vectors and Euclidean distance comparison, the system identifies individuals in real time, prevents duplicate registrations, logs arrival timestamps, and compiles automated Excel reports.

---

## System Interface & Verification Gallery

<table align="center">
  <tr>
    <td align="center"><b>Real-Time Facial Detection Interface</b><br><sub>Spatial landmark tracking with confidence bounding boxes.</sub></td>
    <td align="center"><b>Biometric Identity Verification</b><br><sub>Instantaneous candidate verification against encoded face database.</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235618.png" alt="Detection UI" width="460"/></td>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235707.png" alt="Verification UI" width="460"/></td>
  </tr>
  <tr>
    <td align="center"><b>Automated Attendance Timestamp Log</b><br><sub>Immutable attendance session logging and daily attendance records.</sub></td>
    <td align="center"><b>Student Registration & Management</b><br><sub>Enrollment portal for capturing training image sets.</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235747.png" alt="Log Table" width="460"/></td>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235812.png" alt="Management UI" width="460"/></td>
  </tr>
</table>

---

## System Architecture

```mermaid
flowchart TD
    A[Live Camera Video Stream] --> B[Haar Cascade / HOG Face Detection]
    B --> C[68-Point Facial Landmark Alignment]
    C --> D[128-Dimensional Deep Feature Embedding]
    D --> E[Vector Distance Matcher vs Local Student Encodings]
    E -->|Confidence Above Threshold| F[Verification Confirmed & Audio Confirmation]
    E -->|Confidence Below Threshold| G[Unknown Face Alert]
    F --> H[SQLite & Excel Attendance Record Write]
    H --> I[Web Dashboard Visualization]
```

---

## Technology Stack

| Domain | Technologies |
| :--- | :--- |
| Vision Frameworks | OpenCV, Face Recognition, Dlib |
| Core Language | Python 3.10+ |
| Web Application | Flask, HTML5, CSS3, JavaScript |
| Data Export | Pandas, OpenPyXL |

---

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/sohailahmed-bsrh/smart-attendance-system.git
cd smart-attendance-system

# Install dependencies
pip install -r requirements.txt

# Encode student face database
python encode_faces.py

# Launch attendance verification system
python main.py
```

---

## Author & License

- **Author**: Sohail Ahmed ([Portfolio](https://sohail.devsil.com) | [GitHub](https://github.com/sohailahmed-bsrh))
- **License**: Distributed under the MIT License.
