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
                fallbackScript: [script: 'return ["error"]'], 
                script: [script: 'return ["1.0", "2.0", "3.0"]']
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
                fallbackScript: [script: 'return ["error"]'], 
                script: [script: '''
                    // The matrix logic
                    def matrix = [
                        "1.0": ["1.0", "1.1"],
                        "2.0": ["2.0", "2.1-beta"],
                        "3.0": ["3.0", "3.1"]
                    ]
                    
                    // 'BACKEND_VERSION' is automatically available as a variable
                    return matrix[BACKEND_VERSION] ?: ["No compatible versions found"]
                ''']
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

        // stage('Ensure Dependencies Installed') {
        //     steps {
        //     }
        // }

        stage('Create Client Infrastructure via Terraform') {
            steps {
            }
        }

        stage('Move Key to .ssh Folder') {
            steps {
            }
        }

        stage('Configure Client Product via Ansible') {
            steps {
            }
        }

        stage('Execute Validation Tests') {
            steps {
            }
        }
    }

    post {
        success {
            echo "Successfully deployed ${params.CLIENT_NAME}"
            echo "Sending FE ALB Hostname to ${params.CLIENT_EMAIL}"
            script {
                ********************//def alb_url = sh(script: "terraform output -raw frontend_alb_dns", returnStdout: true).trim()
                
                mail to: "${params.CLIENT_EMAIL}",
                    subject: "Your DMS Environment is Ready: ${params.CLIENT_NAME}",
                    body: "Hello,\n\nYour DMS environment has been deployed.\nURL: http://${alb_url}\n"
            }
        }
        failure {
            echo "Tests failed — showing logs:"
            sh "docker logs ${CONTAINER_NAME} || true"
        }

        always {
            echo "Cleaning up..."
            sh """
                docker rm -f ${CONTAINER_NAME} || true
                docker rmi ${REGISTRY}/${IMAGE_NAME}:${env.TAG} || true
                docker system prune -af --volumes || true
            """
            deleteDir()
        }
    }

}