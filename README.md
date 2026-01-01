# Domain Monitoring System - DevOps Course

A domain monitoring system project for DevOps course.

## 📌 Project Description

This system monitors the availability and status of domains. It includes user management, logging, domain management, domain monitoring and web interface support.

## 🧱 Project Structure

```
domain_monitoring_devops/
├── app.py                    # Web interface (Flask)
├── DomainManagementEngine.py # Domain management logic
├── MonitoringSystem.py       # Domain monitoring engine
├── UserManagementModule.py   # User management
├── logger.py                 # Logging system
├── templates/                # dynamic dashboard HTML template
├── static/                   # Static files (HTML, CSS, JS)
├── tests/                    # Test and demo files
├── logs/                     # Log folder
└── UsersData/                # User data
```

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/MatanItzhaki12/domain_monitoring_devops.git
cd domain_monitoring_devops
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv # Or: python3 -m venv venv
source venv/bin/activate  # On Windows (CMD): venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the main file (e.g., app.py):

```bash
python app.py
```

* You can also run the performance test file in `tests/`:

```bash
python tests/test_monitoring_system.py
```

## 👤 Authors

* Matan
* Sergey
* Johhny
* Oz
* Assaf

## 📄 License

This project is licensed under the MIT License.

# test 2

