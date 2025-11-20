pipeline {
    agent { label 'Slave' }

    environment {
        REGISTRY = "symmetramain"
        IMAGE_NAME = "etcsys"
        REPO_URL = "https://github.com/MatanItzhaki12/domain_monitoring_devops.git"
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
                    // Retrieve commit hash
                    def commit = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    echo "Commit ID: ${commit}"

                    // Prepare version tag
                    def b = BUILD_NUMBER.toInteger()
                    def shortTag = commit.take(8)

                    env.VERSION_TAG = "build-${b}-${shortTag}"
                    env.TAG = shortTag

                    echo "Build version: ${env.VERSION_TAG}"
                }
            }
        }

        stage('Build Docker Image (temp)') {
            steps {
                echo "Building Docker image: ${REGISTRY}/${IMAGE_NAME}:${env.TAG}"
                sh """
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:${env.TAG} .
                """
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
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

                stage('UI Selenium Tests') {
                    steps {
                        echo "Running Selenium UI tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/selenium_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

            }
        }

        stage('Promote Version and Push to DockerHub') {
            when { expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' } }

            steps {
                script {

                    echo "Promoting version..."

                    // Detect latest tag
                    def currentVersion = sh(
                        script: "git tag --sort=-v:refname | grep -Eo 'v[0-9]+\\.[0-9]+\\.[0-9]+' | head -n1 || echo 'v0.0.0'",
                        returnStdout: true
                    ).trim()

                    echo "Current version: ${currentVersion}"

                    def parts = currentVersion.replace('v', '').tokenize('.')
                    def major = parts.size() > 0 ? parts[0].toInteger() : 0
                    def minor = parts.size() > 1 ? parts[1].toInteger() : 0
                    def patch = parts.size() > 2 ? parts[2].toInteger() : 0

                    def newVersion = "v${major}.${minor}.${patch + 1}"
                    echo "New version: ${newVersion}"

                    // DockerHub Authentication and Push
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

                    // GitHub Tagging
                    withCredentials([usernamePassword(
                        credentialsId: 'github-token',
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {

                        sh """
                            git config --global user.email "jenkins@ci.local"
                            git config --global user.name "Jenkins CI"
                            git tag -a ${newVersion} -m 'Release ${newVersion}'
                            git push https://${GIT_USER}:${GIT_TOKEN}@github.com/cerform/domain_monitoring_devops.git ${newVersion}
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
