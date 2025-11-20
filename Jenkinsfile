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
                    def commit = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    echo "Commit ID: ${commit}"

                    def b = BUILD_NUMBER.toInteger()
                    def short = commit.take(8)

                    env.TAG = short
                    env.VERSION_TAG = "build-${b}-${short}"

                    echo "Build version: ${env.VERSION_TAG}"
                }
            }
        }

        stage('Prepare Test Environment') {
            steps {
                echo "Cleaning UsersData before tests..."
                sh """
                    mkdir -p UsersData
                    echo "[]" > UsersData/users.json
                    find UsersData -name "*_domains.json" -delete || true
                """
            }
        }

        stage('Build Docker Image') {
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
                    docker run -d --name ${CONTAINER_NAME} -p 8080:8080 ${REGISTRY}/${IMAGE_NAME}:${env.TAG}
                """

                echo "Waiting for Flask backend to start..."
                sh "sleep 5"
            }
        }

        stage('Execute Tests') {
            parallel {

                stage('API Tests') {
                    steps {
                        echo "Running backend API tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

                stage('UI Selenium Tests') {
                    steps {
                        echo "Running UI Selenium tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/selenium_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

            }
        }

        stage('Promote Version & Push') {
            when { expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' } }
            steps {
                script {

                    // detect latest version
                    def currentVersion = sh(
                        script: "git tag --sort=-v:refname | grep -Eo 'v[0-9]+\\.[0-9]+\\.[0-9]+' | head -n1 || echo 'v0.0.0'",
                        returnStdout: true
                    ).trim()

                    echo "Current version: ${currentVersion}"

                    def (major, minor, patch) = currentVersion.replace('v', '').tokenize('.').collect { it.toInteger() }
                    def newVersion = "v${major}.${minor}.${patch + 1}"

                    echo "New version: ${newVersion}"

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

    } // stages

    post {

        failure {
            echo "Tests FAILED — printing logs..."
            sh "docker logs ${CONTAINER_NAME} || true"
        }

        always {
            echo "Cleaning temp containers & images..."
            sh """
                docker rm -f ${CONTAINER_NAME} || true
                docker rmi ${REGISTRY}/${IMAGE_NAME}:${env.TAG} || true
                docker system prune -af --volumes || true
            """
            deleteDir()
        }
    }
}
