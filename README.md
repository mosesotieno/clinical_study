# 🏥 Clinical Study Management System

[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-blue.svg)](https://getbootstrap.com/)
[![Font Awesome](https://img.shields.io/badge/Icons-Font%20Awesome-lightgrey.svg)](https://fontawesome.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modern, streamlined **Django-based web application** designed to manage clinical studies efficiently.  
The system provides a complete workflow for **participant enrollment, visit tracking, assessments, lab requests, and reporting** — all within an intuitive interface powered by **Bootstrap 5** and **Font Awesome**.

---

## 🚀 Features

- **Participant Management**
  - Enroll new participants  
  - View participant profiles  
  - Search and filter participants  

- **Visit Workflow**
  - Track **Active Visits** and **Completed Visits**  
  - Manage station-based workflow:
    - 🩺 Vitals Station  
    - 👨‍⚕️ Doctor Assessment  
    - 🧠 Psychiatry  
    - 🧪 Lab Requests  

- **Reports & Analytics**
  - 📊 Study Progress Report  
  - 📝 Visit Summary  
  - 📂 Participant Data Export  

- **Quick Actions**
  - Enroll new participants in one click  
  - Find participants easily  
  - View real-time queue of visits  

- **User Management**
  - Secure authentication  
  - Role-based access to workflows  
  - User-friendly navigation  

---

## 🖼️ User Interface Highlights

- **Responsive Navbar** with quick access to Dashboard, Participants, Visits, and Enrollment  
- **Sidebar Navigation** grouping workflow stations, visit management, reports, and quick actions  
- **Status Indicators** for completed and ongoing workflow steps  
- **Clean Bootstrap 5 Styling** for consistent UI/UX  
- **Message Alerts** with dismissible notifications  

---

## ⚙️ Tech Stack

- **Backend**: Django (Python)  
- **Frontend**: Bootstrap 5, Font Awesome  
- **Database**: PostgreSQL / SQLite (configurable)  
- **Authentication**: Django’s built-in auth system  
- **Reports & Data Export**: Django ORM + custom templates  

---

## 📂 Project Structure

clinical_study/
├── core/                 # Core app with models, views, templates
├── templates/            # Base and extended templates
│   └── base.html         # Main layout file
├── static/               # Static assets (CSS, JS, images)
├── manage.py             # Django project runner
|── requirements.txt      # Required modules
└── README.md             # Project documentation
