pipeline {

    agent { label 'Slave' }

    options {
        timestamps()
        disableRestartFromStage()   // ❗ запрещает Restart from Stage
    }

    environment {
        REGISTRY        = "symmetramain"
        IMAGE_NAME      = "etcsys"
        REPO_URL        = "https://github.com/cerform/domain_monitoring_devops.git"
        CONTAINER_NAME  = "temp_container_${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Source Code') {
            steps {
                echo "Cloning repository..."
                git branch: 'main', url: "${REPO_URL}"
            }
        }

        stage('Get Commit ID') {
            steps {
                script {
                    def commit = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    echo "Commit ID: ${commit}"
                    env.TAG = commit.take(8)
                    echo "Docker tag: ${env.TAG}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh """
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:${env.TAG} .
                """
            }
        }

        stage('Run Container for Tests') {
            steps {
                echo "Starting container for tests..."
                sh """
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d --name ${CONTAINER_NAME} ${REGISTRY}/${IMAGE_NAME}:${env.TAG}
                """
            }
        }

        stage('Execute Tests') {
            parallel {

                stage('Backend API Tests') {
                    steps {
                        echo "Running API tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/api_tests \
                                --maxfail=1 --disable-warnings -q
                        """
                    }
                }

                stage('Selenium UI Tests') {
                    steps {
                        echo "Running Selenium tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/selenium_tests \
                                --maxfail=1 --disable-warnings -q
                        """
                    }
                }

            }
        }

        stage('Promote and Push Image') {
            steps {
                script {

                    echo "Detecting latest version tag..."

                    def lastTag = sh(
                        script: "git tag --sort=-v:refname | grep -Eo 'v[0-9]+\\.[0-9]+\\.[0-9]+' | head -n1 || true",
                        returnStdout: true
                    ).trim()

                    if (!lastTag) {
                        echo "No tags found — starting from v0.0.0"
                        lastTag = "v0.0.0"
                    }

                    echo "Current version: ${lastTag}"

                    def (major, minor, patch) = lastTag.replace("v", "").tokenize('.').collect { it.toInteger() }
                    def newVersion = "v${major}.${minor}.${patch + 1}"

                    echo "New version: ${newVersion}"

                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {

                        sh """
                            echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                            docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:${newVersion}
                            docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:latest
                            docker push \$DOCKER_USER/${IMAGE_NAME}:${newVersion}
                            docker push \$DOCKER_USER/${IMAGE_NAME}:latest
                            docker logout
                        """
                    }

                    // Push GitHub tag
                    withCredentials([usernamePassword(
                        credentialsId: 'github-token',
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {
                        sh """
                            git config --global user.email "jenkins@ci.local"
                            git config --global user.name "Jenkins CI"
                            git tag -a ${newVersion} -m 'Release ${newVersion}'
                            git push https://\${GIT_USER}:\${GIT_TOKEN}@github.com/cerform/domain_monitoring_devops.git ${newVersion}
                        """
                    }
                }
            }
        }

    }

    post {

        failure {
            echo "Tests failed — showing container logs"
            sh "docker logs ${CONTAINER_NAME} || true"
        }

        always {
            echo "Cleaning up environment..."
            sh """
                docker rm -f ${CONTAINER_NAME} || true
                docker rmi ${REGISTRY}/${IMAGE_NAME}:${env.TAG} || true
                docker system prune -af --volumes || true
            """
            deleteDir()
        }
    }
}
