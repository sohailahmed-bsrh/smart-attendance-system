<div align="center">

<h1>Smart Biometric Attendance Verification System</h1>

<img src="https://readme-typing-svg.herokuapp.com?font=Inter&weight=800&size=22&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&width=800&lines=Facial+Biometric+Verification+Engine;Real-Time+Landmark+Tracking;Automated+Logging+%26+Excel+Reporting;Desktop+GUI+%2B+Web+Management+Console" alt="Typing Header" />

<p><strong>Real-Time Facial Recognition Attendance Management System with Anti-Spoofing Architecture</strong></p>

<p>
  <a href="https://skillicons.dev"><img src="https://skillicons.dev/icons?i=python,opencv,flask,github&theme=dark" alt="Skills" /></a>
</p>

<p>
  <a href="#overview">Overview</a> &bull;
  <a href="#system-architecture">Architecture</a> &bull;
  <a href="#visual-showcase-gallery">Visual Gallery</a> &bull;
  <a href="#core-capabilities">Capabilities</a> &bull;
  <a href="#installation--setup">Installation</a> &bull;
  <a href="#author--contact-information">Author</a>
</p>

</div>

---
## Overview

The Smart Biometric Attendance Verification System replaces manual record-keeping with automated computer vision authentication. Utilizing 128-dimensional facial embedding vectors and Euclidean distance comparison, the system identifies individuals in real time, prevents duplicate registrations, logs arrival timestamps, and compiles automated Excel reports.

---

## Visual Showcase Gallery

<table width="100%" align="center">
  <tr>
    <td width="50%" align="center"><b>Real-Time Facial Detection Interface</b><br><sub>Spatial landmark tracking with confidence bounding boxes.</sub></td>
    <td width="50%" align="center"><b>Biometric Identity Verification</b><br><sub>Instantaneous candidate verification against encoded face database.</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235618.png" alt="Detection UI" width="460"/></td>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235707.png" alt="Verification UI" width="460"/></td>
  </tr>
  <tr>
    <td width="50%" align="center"><b>Automated Attendance Timestamp Log</b><br><sub>Immutable attendance session logging and daily attendance records.</sub></td>
    <td width="50%" align="center"><b>Student Registration & Management</b><br><sub>Enrollment portal for capturing training image sets.</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235747.png" alt="Log Table" width="460"/></td>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235812.png" alt="Management UI" width="460"/></td>
  </tr>
  <tr>
    <td width="50%" align="center"><b>Analytics & Attendance Reporting</b><br><sub>Visual statistical reporting on student arrival trends.</sub></td>
    <td width="50%" align="center"><b>System Configuration & Thresholds</b><br><sub>Customizable Euclidean distance thresholds and camera settings.</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235825.png" alt="Reporting UI" width="460"/></td>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235839.png" alt="Settings UI" width="460"/></td>
  </tr>
  <tr>
    <td width="50%" align="center"><b>Excel Spreadsheet Export Engine</b><br><sub>One-click export formatting official institutional attendance sheets.</sub></td>
    <td width="50%" align="center"><b>Student Facial Dataset Sample</b><br><sub>Enrolled student training image verified in local biometric database.</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="screenshots/Screenshot%202026-08-05%20235856.png" alt="Export UI" width="460"/></td>
    <td align="center"><img src="student_images/sohail%20ahmed/1.jpg" alt="Student Sample" width="460"/></td>
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

## Author & Contact Information

<table width="100%" align="center">
  <tr>
    <td align="center" style="padding: 20px;">
      <h3>Sohail Ahmed</h3>
      <p><strong>Full-Stack Artificial Intelligence & Computer Vision Engineer</strong></p>
      <p>
        <a href="https://sohail.devsil.com"><img src="https://img.shields.io/badge/Live_Portfolio-sohail.devsil.com-0052FF?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Portfolio"/></a>
        <a href="https://github.com/sohailahmed-bsrh"><img src="https://img.shields.io/badge/GitHub-Profile-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a>
        <a href="https://linkedin.com/in/sohail-ahmed-dev"><img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/></a>
        <a href="mailto:sohail.bsrh@gmail.com"><img src="https://img.shields.io/badge/Email-Contact_Me-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"/></a>
      </p>
      <p><em>Available for technical roles in Artificial Intelligence, Computer Vision, and Full-Stack Engineering.</em></p>
      <hr style="border: 0; height: 1px; background: #30363d; margin: 15px 0;">
      <small>Repository: <code>sohailahmed-bsrh/smart-attendance-system</code> &bull; Distributed under the MIT License.</small>
    </td>
  </tr>
</table>
