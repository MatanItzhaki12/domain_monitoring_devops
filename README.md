# Domain Monitoring System - Backend

This repository contains the backend service for the Domain Monitoring System, developed as part of a DevOps course project.

## 📌 Project Description

The backend monitors the availability and status of domains. It provides REST APIs for domain management, user management, logging, and monitoring operations. The backend is built with Python (Flask) and is designed for integration with CI/CD pipelines and infrastructure automation.

## 🧱 Backend Structure

```
domain_monitoring_backend/
├── app.py                    # Main Flask application (API server)
├── DomainManagementEngine.py # Domain management logic
├── MonitoringSystem.py       # Domain monitoring engine
├── UserManagementModule.py   # User management logic
├── logger.py                 # Logging system
├── tests/                    # Backend tests (API, performance, etc.)
├── logs/                     # Log files
└── UsersData/                # User data storage
```

## ⚙️ Installation & Usage

1. Clone the repository:

```bash
git clone https://github.com/MatanItzhaki12/domain_monitoring_devops.git
cd domain_monitoring_devops
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

3. Run the backend server:

```bash
python app.py
```

4. (Optional) Run backend tests:

```bash
python -m unittest discover tests
# or
pytest tests/
```

## 👤 Authors

- Matan
- Sergey
- Johhny
- Oz
- Assaf

## 📄 License

This project is licensed under the MIT License.