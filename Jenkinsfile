pipeline {
    agent { label 'Slave' }

    environment {
        REGISTRY = "dms"
        IMAGE_NAME = "dms_image"
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
                    def shortTag = commit.take(8)

                    env.TAG = shortTag
                    env.VERSION_TAG = "build-${b}-${shortTag}"

                    echo "Image tag: ${env.TAG}"
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

        stage('Run Container for Tests') {
            steps {
                echo "Starting temporary container..."
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
                        echo "Running backend API tests..."
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

                // -------------- SELENIUM STUB TESTS --------------------
                stage('UI Selenium Tests (Stub)') {
                    steps {
                        echo "Running STUB Selenium tests..."

                        sh """
                           
                            docker exec ${CONTAINER_NAME} sh -c "mkdir -p /app/tests/selenium_tests"

                           
                            docker exec ${CONTAINER_NAME} sh -c "echo 'def test_stub(): assert True' > /app/tests/selenium_tests/test_stub.py"

                           
                            docker exec ${CONTAINER_NAME} pytest /app/tests/selenium_tests/test_stub.py -q
                        """
                    }
                }

            }
        }

        stage('Promote and Push Image') {
            when { expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' } }

            steps {
                script {
                    echo "Detecting latest version tag..."

                    def latestTag = sh(
                        script: "git tag --sort=-v:refname | grep -Eo 'v[0-9]+\\.[0-9]+\\.[0-9]+' | head -n1 || echo 'v0.0.0'",
                        returnStdout: true
                    ).trim()

                    echo "Current version: ${latestTag}"
                    if (latestTag == '') {
                        latestTag = 'v0.0.0'
                    }
                    def parts = latestTag.replace('v','').tokenize('.')
                    def major = parts[0].toInteger()
                    def minor = parts[1].toInteger()
                    def patch = parts[2].toInteger()

                    def newVersion = "v${major}.${minor}.${patch + 1}"
                    echo "New version: ${newVersion}"

                    // Push image to DockerHub
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

                    // Push git tag
                    withCredentials([usernamePassword(
                        credentialsId: 'github-token',
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {

                        sh """
                            git config --global user.email "jenkins@ci.local"
                            git config --global user.name "Jenkins CI"
                            git tag -a ${newVersion} -m 'Release ${newVersion}' || true
                            git push https://\$GIT_USER:\$GIT_TOKEN@github.com/cerform/domain_monitoring_devops.git ${newVersion} || true
                        """
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