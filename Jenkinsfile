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
                echo "Cloning repository..."
                git branch: 'main', url: "${REPO_URL}"
            }
        }

        stage('Get Commit ID') {
            steps {
                script {
                    def commit = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    echo "Commit: ${commit}"

                    def shortTag = commit.take(8)
                    env.TAG = shortTag
                    echo "TAG: ${env.TAG}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:${env.TAG} .
                """
            }
        }

        stage('Run Container for Tests') {
            steps {
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
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q
                        """
                    }
                }

                stage('Selenium UI Tests') {
                    steps {
                        sh """
                            docker exec ${CONTAINER_NAME} pytest tests/selenium_tests --maxfail=1 --disable-warnings -q
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

                    def currentVersion = sh(
                        script: """
                            git tag --sort=-v:refname | grep -E 'v[0-9]+\\.[0-9]+\\.[0-9]+' | head -n1
                        """,
                        returnStdout: true
                    ).trim()

                    if (!currentVersion) {
                        currentVersion = "v0.0.0"
                        echo "No tags found — starting from v0.0.0"
                    }

                    echo "Current version: ${currentVersion}"

                    def parts = currentVersion.replace("v","").split("\\.")
                    def major = parts[0] as Integer
                    def minor = parts[1] as Integer
                    def patch = parts[2] as Integer

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

    }

    post {
        failure {
            echo "Tests failed — showing logs"
            sh "docker logs ${CONTAINER_NAME} || true"
        }

        always {
            sh """
                docker rm -f ${CONTAINER_NAME} || true
                docker rmi ${REGISTRY}/${IMAGE_NAME}:${env.TAG} || true
                docker system prune -af --volumes || true
            """
            deleteDir()
        }
    }
}
