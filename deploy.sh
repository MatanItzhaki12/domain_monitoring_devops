#!/bin/bash

function check_result() {
    if [ $? -ne 0 ]; then
        echo "[ERROR] $1 failed. Exiting."
        exit 1
    fi
    echo "[SUCCESS] $1 succeeded."
}
echo "Starting system updates and upgrades"

sudo apt update -y &>/dev/null 
check_result "System update completed"

sudo apt install python3.12-venv -y &>/dev/null
check_result "Venv Dependency installed"


if [ ! -d "/opt/domain_monitoring_devops" ]; then
    git clone https://github.com/MatanItzhaki12/domain_monitoring_devops.git &>/dev/null 
    check_result "Cloned Git Repository"   
else echo "Repo already exists"
fi 


# sudo chmod 777 domain_monitoring_devops
# check_result "Permissions changed"

sudo mv domain_monitoring_devops/ /opt/
check_result "Moved folder to Opt"

python3 -m venv /opt/domain_monitoring_devops/_venv_
check_result "Venv created"

source /opt/domain_monitoring_devops/_venv_/bin/activate
check_result "Venv activated"

pip install -r /opt/domain_monitoring_devops/requirements.txt &>/dev/null 
check_result "Requirements installed to venv"

cat<<EOF>> /opt/domain_monitoring_devops/run.sh
#!/bin/bash
#
source /opt/domain_monitoring_devops/_venv_/bin/activate
python3 /opt/domain_monitoring_devops/app.py
EOF


sudo chmod +x /opt/domain_monitoring_devops/run.sh
check_result "permission changed for run.sh"

cat<<EOF>> dms.service
[Unit]
Description=Group2_DMS
After=network.target

[Service]
WorkingDirectory=/opt/domain_monitoring_devops
ExecStart=/opt/domain_monitoring_devops/run.sh
Type=simple
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo mv dms.service /etc/systemd/system/
check_result "service created & moved"

sudo systemctl daemon-reload
sudo systemctl enable dms.service
sudo systemctl start dms.service
check_result "service enabled & started"

sudo systemctl status dms.service | grep 8080

