properties([
    parameters([
        string(name: 'CLIENT_NAME', defaultValue: '', 
                description: 'REQUIRED: Enter client name (lowercase, no spaces, e.g., "acme-corp")')        
        string(name: 'CLIENT_EMAIL', defaultValue: '', 
                description: 'REQUIRED: Enter client email')        
        string(name: 'BACKEND_VM_COUNT', defaultValue: '1'),
        string(name: 'FRONTEND_VM_COUNT', defaultValue: '2'),
        // Parent Parameter: Backend Version
        [$class: 'ChoiceParameter', 
            name: 'BACKEND_VERSION', 
            choiceType: 'PT_SINGLE_SELECT', 
            description: 'Select Backend Version',
            script: [
                $class: 'GroovyScript', 
                sandbox: false,
                fallbackScript: [script: 'return ["error"]'], 
                script: [
                    script: '''
                        import groovy.json.JsonSlurper
                        def url = new URL (
                        "https://raw.githubusercontent.com/MatanItzhaki12/domain_monitoring_devops/versions/matrix.json"
                        )
                        def json = new JsonSlurper().parse(url)

                        // returning backends keys:
                        return json.backend.keySet().sort()
                    '''
                ]
            ]
        ],
        // Reactive Parameter: Frontend Version (Depends on BACKEND_VERSION)
        [$class: 'CascadeChoiceParameter', 
            name: 'FRONTEND_VERSION', 
            choiceType: 'PT_SINGLE_SELECT', 
            description: 'Select compatible Frontend Version',
            referencedParameters: 'BACKEND_VERSION', 
            script: [
                $class: 'GroovyScript', 
                sandbox: false,
                fallbackScript: [script: 'return ["error"]'], 
                script: [
                    script: '''
                        import groovy.json.JsonSlurper
                        
                        if (!BACKEND_VERSION) {
                            return ['Select backend version']
                        }

                        def url = new URL (
                        "https://raw.githubusercontent.com/MatanItzhaki12/domain_monitoring_devops/versions/matrix.json"
                        ) 

                        def json = new JsonSlurper().parse(url)

                        // returning frontend version correcsponding to the backend version:
                        frontend_versions = json.backend[BACKEND_VERSION]
                        return frontend_versions ? frontend_versions.sort() : ["No compatible versions found"]
                    '''
                ]
            ]
        ]
    ])
])

pipeline {
    agent any

    environment {
        REGISTRY = "matan8520"
        IMAGE_NAME = "dms_frontend"
        REPO_URL = "https://github.com/MatanItzhaki12/domain_monitoring_devops.git"
        REPO_URL_NO_HTTP = "github.com/MatanItzhaki12/domain_monitoring_devops.git"
    }

    options { 
        timestamps()
        disableConcurrentBuilds()
        ansiColor('xterm') // Enables colors in logs
    }

    stages {

        stage('Validate Parameters') {
            steps {
                script {
                    // Client Name Validation
                    if (params.CLIENT_NAME == null || params.CLIENT_NAME.trim() == "") {
                        error "STOPPING: CLIENT_NAME is required. Please provide a unique client identifier."
                    }
                    // Regex to ensure AWS compatibility (no spaces/special chars)
                    if (!(params.CLIENT_NAME =~ /^[a-z0-9-]+$/)) {
                        error "STOPPING: CLIENT_NAME must be lowercase alphanumeric and hyphens only (e.g., 'client-alpha')."
                    }

                    // Client Email Address Validation
                    if (!params.CLIENT_EMAIL?.trim()) {
                        error "STOPPING: CLIENT_EMAIL is required."
                    }
                    def emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/
                    if (!(params.CLIENT_EMAIL =~ emailPattern)) {
                        error "STOPPING: '${params.CLIENT_EMAIL}' is not a valid email address."
                    }

                    // Backend VM Count Validation
                    if (!params.BACKEND_VM_COUNT.isInteger() || params.BACKEND_VM_COUNT.toInteger() < 1) {
                        error "BACKEND_VM_COUNT must be a positive integer (received: ${params.BACKEND_VM_COUNT})"
                    }
                    // Frontend VM Count Validation
                    if (!params.FRONTEND_VM_COUNT.isInteger() || params.FRONTEND_VM_COUNT.toInteger() < 1) {
                        error "FRONTEND_VM_COUNT must be a positive integer (received: ${params.FRONTEND_VM_COUNT})"
                    }

                    // Limit the maximum to prevent massive accidental AWS bills
                    if (params.BACKEND_VM_COUNT.toInteger() > 1) {
                        error "BACKEND_VM_COUNT exceeds maximum limit of 1 for single-tenant deployments."
                    }
                    if (params.FRONTEND_VM_COUNT.toInteger() > 6) {
                        error "FRONT_VM_COUNT exceeds maximum limit of 6 for single-tenant deployments."
                    }
                }
            }
        }

        stage('Show Release Parameters') {
            steps {
                echo """
                ==================================================
                Client Name        : ${params.CLIENT_NAME}
                Backend Version    : ${params.BACKEND_VERSION}
                Frontend Version   : ${params.FRONTEND_VERSION}
                Backend VM Count   : ${params.BACKEND_VM_COUNT}
                Frontend VM Count  : ${params.FRONTEND_VM_COUNT}
                ==================================================
                """
            }
        }

        stage('Checkout Source Code') {
            steps {
                echo "Cloning repository from GitHub..."
                git branch: 'Prod-Infra', url: "${REPO_URL}"
                sh 'ls'
            }
        }

        stage('Ensure Dependencies Installed') {
            steps {
                sh '''
                    set -e

                    echo "Checking Python, Terraform, and Ansible installations..."

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
                
                '''
            }
        }

        stage('Create Client Infrastructure via Terraform') {
            steps {
                withAWS(credentials: 'aws-creds'){
                    sh """
                        set -e

                        cd $WORKSPACE/Terraform/environment

                        echo "Writing Variables to terraform.tfvars"
                        cat > "terraform.tfvars" <<EOF
                        # environment
                        group_name = "Group2"
                        environment = "${params.CLIENT_NAME}"

                        # networking
                        vpc_cidr = "10.11.0.0/16"
                        public_subnet_cidr = "10.11.1.0/24"
                        private_subnet_cidr = "10.11.2.0/24"

                        # security
                        ssh_public_key_name = "group2_${params.CLIENT_NAME}_dms_pubkey"
                        ssh_private_key_name = "group2_${params.CLIENT_NAME}_private_key"

                        # compute
                        os_ami = "ami-0f5fcdfbd140e4ab7"
                        ec2_type = "t3.small"
                        fe_machines = ${params.FRONTEND_VM_COUNT.toInteger()}
                        be_machines = ${params.BACKEND_VM_COUNT.toInteger()}
                        EOF

                        terraform init -input=false
                        terraform plan -input=false -out=tfplan
                        terraform apply -input=false tfplan --auto-approve
                    """
                }
            }
        }

        stage('Move Key to .ssh Folder') {
            steps {
                sh """
                    set -e

                    KEY_FILE_NAME="group2_${params.CLIENT_NAME}_private_key.pem"
                    SRC="$WORKSPACE/Terraform/environment/keys/$KEY_FILE_NAME"
                    DEST="$HOME/.ssh/keys/$KEY_FILE_NAME"

                    mkdir -p "$HOME/.ssh/keys"
                    chmod 700 "$HOME/.ssh"
                    chmod 700 "$HOME/.ssh/keys"
                    
                    if [ -f "$DEST" ]; then
                        rm -f "$DEST"
                    fi

                    cp "$SRC" "$DEST"
                    chmod 600 "$DEST"
                """
            }
        }

        stage('Configure Client Product via Ansible') {
            steps {
                withCredentials([string(credentialsId: 'ansible-vault-password', variable: 'VAULT_PASS')]){
                    sh """
                        set -e

                        cd $WORKSPACE/Ansible/

                        VAULT_FILE=$(mktemp)
                        echo "$VAULT_PASS" > "$VAULT_FILE"
                        chmod 600 "$VAULT_FILE"

                        ansible-playbook playbook.yaml -i inventory/aws_ec2.yml \
                        --vault-password-file "$VAULT_FILE"

                        rm -f "$VAULT_FILE"
                    """
                }
                
            }
        }

        stage('Execute Validation Tests') {
            steps {
                sh """
                    set -e

                    cd $WORKSPACE/tests/

                    if [ ! -d "venv" ]; then
                        python3 -m venv venv
                    fi

                    # Activate venv and install dependencies
                    source venv/bin/activate
                    pip install -r requirements.txt

                    # Run tests
                    pytest tests/ --maxfail=1 --disable-warnings -q
                """
            }
        }
    }

    post {
        success {
            echo "Successfully deployed ${params.CLIENT_NAME}"
            echo "Sending FE ALB Hostname to ${params.CLIENT_EMAIL}"
            script {
                def alb_url = sh(script: """
                    cd $WORKSPACE/Terraform/environment
                    terraform output -raw frontend_alb_dns
                    """, returnStdout: true).trim()
                
                emailext to: "${params.CLIENT_EMAIL}",
                    subject: "Your DMS Environment is Ready: ${params.CLIENT_NAME}",
                    body: "Hello,\n\nYour DMS environment has been deployed.\nURL: http://${alb_url}\n"
            }
        }

        failure {
            echo "Failure: Terraform will destroy resoueces."
            sh """
                cd $WORKSPACE/Terraform/environment
                terraform init -input=false
                terraform destroy -input=false tfplan --auto-approve
            """
            echo "Terraform Destroyed Resources Successfully!"
        }

        always {
            echo "Cleaning up..."
            deleteDir()
        }
    }

}