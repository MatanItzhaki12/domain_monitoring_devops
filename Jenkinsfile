pipeline {
    agent any

    environment {
        REGISTRY = "matan8520"
        IMAGE_NAME = "dms_frontend"
        REPO_URL = "https://github.com/MatanItzhaki12/domain_monitoring_devops.git"
        REPO_URL_NO_HTTP = "github.com/MatanItzhaki12/domain_monitoring_devops.git"
        CONTAINER_NAME = "temp_container_${BUILD_NUMBER}"
    }

    options { timestamps() }

    stages {

        stage('Checkout Source Code') {
            steps {
                echo "Cloning repository from GitHub..."
                git branch: 'frontend', url: "${REPO_URL}"
            }
        }

        stage('Get Commit ID') {
            steps {
                script {
                    def commit = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    echo "Commit ID: ${commit}"
                    env.TAG = commit.take(8)
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image ${REGISTRY}/${IMAGE_NAME}:${env.TAG}"
                sh """
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:${env.TAG} .
                """
            }
        }

        stage('Setup Network') {
                    steps {
                        // Create a bridge network so containers can see each other
                        sh 'docker network create dms_network || true'
                    }
        }

        stage('Run Backend Container') {
            steps {
                echo "Starting backend container..."
                sh """
                    docker rm -f backend_test_container || true
                    
                    docker run -d \
                        --name backend_test_container \
                        --network dms_network \
                        -p 8080:8080 \
                        matan8520/dms_backend:latest
                """
            }
        }

        stage('Run Container for Tests') {
            steps {
                echo "Starting frontend/test container..."
                sh """
                    docker rm -f ${CONTAINER_NAME} || true
                    
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --network dms_network \
                        -e BACKEND_IP="backend_test_container" \
                        -e FRONTEND_IP="${CONTAINER_NAME}" \
                        -p 8081:8081 \
                        ${REGISTRY}/${IMAGE_NAME}:${env.TAG}
                """
            }
        }

        stage('Execute Tests') {
            parallel {

                stage('Frontend API Tests') {
                    steps {
                        echo "Running frontend API tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

                // -------------- SELENIUM STUB TESTS --------------------
                stage('UI Selenium Tests') {
                    steps {
                        echo "Running frontend selenium tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/selenium_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

            }
        }

        stage('Compute Semantic Version') {
            steps {
                script {
                    env.NEW_VERSION_TAG = sh(script: '''
                    LATEST_VERSION_DIGEST=$(curl -s 'https://registry.hub.docker.com/v2/repositories/matan8520/dms_frontend/tags?name=latest' \
                                                        | jq -r '.results[0].digest')
                    LATEST_VERSION_TAG=$(curl -s https://registry.hub.docker.com/v2/repositories/matan8520/dms_frontend/tags \
                                                | jq -r --arg d "$LATEST_VERSION_DIGEST" '
                                                .results[]
                                                | select(.digest == $d)
                                                | select(.name | startswith("v"))
                                                | .name
                                            ' | cut -d'v' -f2-)
                    if [ "$LATEST_VERSION_TAG" = "" ]; then 
                        LATEST_VERSION_TAG="0.0.0"
                    fi

                    major=$(echo "$LATEST_VERSION_TAG" | cut -d'.' -f1)
                    minor=$(echo "$LATEST_VERSION_TAG" | cut -d'.' -f2)
                    patch=$(echo "$LATEST_VERSION_TAG" | cut -d'.' -f3)

                    patch=$((patch + 1))

                    echo "v$major.$minor.$patch"
                    ''', returnStdout: true).trim()

                    echo "Calculated Version for pipeline: ${env.NEW_VERSION_TAG}"
                }
            }
        }

        stage('Push Frontend Image') {
            when { expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' } }
            steps {               
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:${env.NEW_VERSION_TAG}
                        docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:latest
                        docker push \$DOCKER_USER/${IMAGE_NAME}:${env.NEW_VERSION_TAG}
                        docker push \$DOCKER_USER/${IMAGE_NAME}:latest
                        docker logout
                    """
                }
            }
        }
        stage('update version matrix file'){
            steps {
                script {
                    env.BACKEND_VERSION = sh(script:'''
                        LATEST_VERSION_DIGEST=$(curl -s 'https://registry.hub.docker.com/v2/repositories/matan8520/dms_backend/tags?name=latest' \
                                                                | jq -r '.results[0].digest')
                            LATEST_VERSION_TAG=$(curl -s https://registry.hub.docker.com/v2/repositories/matan8520/dms_backend/tags \
                                                        | jq -r --arg d "$LATEST_VERSION_DIGEST" '
                                                        .results[]
                                                        | select(.digest == $d)
                                                        | select(.name | startswith("v"))
                                                        | .name
                                                    ' | cut -d'v' -f2-)
                            if [ "$LATEST_VERSION_TAG" = "" ]; then 
                                LATEST_VERSION_TAG="0.0.0"
                            fi
                            echo "v$LATEST_VERSION_TAG"
                        ''', returnStdout: true).trim()
                    echo "Backend version is: ${env.BACKEND_VERSION}"
                    echo "Frontend version is: ${env.NEW_VERSION_TAG}"
                    dir('version_matrix'){
                        git branch: 'versions', url: "${REPO_URL}"
                        sh 'python3 calculate.py'
                        withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                            sh """
                                # Configure Git Identity (Required for commit)
                                git config user.email "jenkins-bot@example.com"
                                git config user.name "Jenkins Bot"

                                # Stage all changes made by the python script
                                git add .

                                # Commit (The '|| echo' prevents failure if there are no changes)
                                git commit -m "Automated update from Jenkins" || echo "No changes to commit"

                                # Push safely using the credentials variables
                                # We inject the token directly into the URL to bypass the password prompt
                                git push https://${GIT_USERNAME}:${GIT_PASSWORD}@${REPO_URL_NO_HTTP} HEAD:versions
                            """
                        }
                    }
                }
            }
        }
    }

    post {
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