echo "Checking Python, Terraform, and Ansible installations and downloding the project from git"

# Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Installing Python3..."
    sudo apt install -y python3 &>/dev/null
fi

# Ensure pip is installed
if ! command -v pip3 >/dev/null 2>&1; then
    echo "Installing pip3..."
    sudo apt install -y python3-pip &>/dev/null
fi

# Ensure venv is installed
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Installing python3-venv..."
    sudo apt install python3-venv -y
fi


# Upgrade modules, if needed
python3 -m pip install --user --upgrade boto3 botocore --break-system-packages &>/dev/null

# # Install boto3 and botocore for AWS Ansible modules
# echo "Installing boto3 and botocore for Ansible AWS integration..."
# sudo apt install -y python3-boto3 python3-botocore >/dev/null

# git
if ! command -v git >/dev/null 2>&1; then
    echo "Installing Git..."
    sudo apt install -y git &>/dev/null
fi

# Terraform
if ! command -v terraform >/dev/null 2>&1; then
    echo "Installing Terraform..."
    sudo apt-get install -y gnupg software-properties-common &>/dev/null
    wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg &>/dev/null
    echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main"\
    | sudo tee /etc/apt/sources.list.d/hashicorp.list &>/dev/null
    sudo apt update &>/dev/null
    sudo apt install -y terraform >/dev/null
fi

# Ansible
if ! command -v ansible >/dev/null 2>&1; then
    echo "Installing Ansible..."
    python3 -m pip install --user --upgrade ansible &>/dev/null
fi