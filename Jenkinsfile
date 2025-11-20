pipeline {
    agent { label 'Slave' }

    environment {
        REGISTRY = "symmetramain"
        IMAGE_NAME = "etcsys"
        REPO_URL = "https://github.com/cerform/domain_monitoring_devops.git"
        CONTAINER_NAME = "temp_container_${BUILD_NUMBER}"
    }

    options { timestamps() }

    stages {

        stage('Checkout Source Code') {
            steps {
                echo "Cloning repository from GitHub..."
                git branch: 'main', url: "${REPO_URL}"
            }
        }

        stage('Get Commit ID') {
            steps {
                script {
                    def commit = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    def shortTag = commit.take(8)
                    env.TAG = shortTag
                    echo "Using commit tag: ${env.TAG}"
                }
            }
        }

        stage('Build Docker Image (temp)') {
            steps {
                echo "Building Docker image: ${REGISTRY}/${IMAGE_NAME}:${env.TAG}"
                sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${env.TAG} ."
            }
        }

        stage('Run Container for Tests') {
            steps {
                echo "Starting temporary container..."
                sh """
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d --name ${CONTAINER_NAME} ${REGISTRY}/${IMAGE_NAME}:${env.TAG}
                """
            }
        }

        stage('Execute Test Suite') {
            parallel {

                stage('Backend API Tests') {
                    steps {
                        echo "Running backend API tests..."
                        sh "docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q"
                    }
                }

                stage('UI Selenium Tests') {
                    steps {
                        echo "Running Selenium UI tests..."
                        sh "docker exec ${CONTAINER_NAME} pytest tests/selenium_tests --maxfail=1 --disable-warnings -q"
                    }
                }

            }
        }

        stage('Promote Version and Push') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }

            steps {
                script {

                    echo "Promoting version..."

                    // Fetch latest tag or fallback to v0.0.0
                    def currentVersion = sh(
                        script: """
                            git fetch --tags
                            git tag --sort=-v:refname \
                            | grep -E 'v[0-9]+\\.[0-9]+\\.[0-9]+' \
                            | head -n 1
                        """,
                        returnStdout: true
                    ).trim()

                    if (!currentVersion) {
                        currentVersion = "v0.0.0"
                        echo "No version tags found, starting from ${currentVersion}"
                    }

                    echo "Current version: ${currentVersion}"

                    def parts = currentVersion.substring(1).tokenize('.')
                    def major = parts[0].toInteger()
                    def minor = parts[1].toInteger()
                    def patch = parts[2].toInteger()

                    def newVersion = "v${major}.${minor}.${patch + 1}"
                    echo "New version: ${newVersion}"

                    // DockerHub Push
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {

                        sh """
                            echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                            docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:${newVersion}
                            docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:latest
                            docker push \$DOCKER_USER/${IMAGE_NAME}:${newVersion}
                            docker push \$DOCKER_USER/${IMAGE_NAME}:latest
                            docker logout
                        """
                    }

                    // GitHub tag push
                    withCredentials([string(credentialsId: 'github-token', variable: 'GIT_TOKEN')]) {

                        sh """
                            git config --global user.email "jenkins@ci.local"
                            git config --global user.name "Jenkins CI"

                            git tag -a ${newVersion} -m "Release ${newVersion}" || true
                            git push https://cerform:\$GIT_TOKEN@github.com/cerform/domain_monitoring_devops.git ${newVersion}
                        """
                    }
                }
            }
        }

    }

    post {

        failure {
            echo "Tests failed. Showing container logs..."
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
