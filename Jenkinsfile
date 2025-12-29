pipeline {
    agent any

    environment {
        REGISTRY = "matan8520"
        IMAGE_NAME = "dms_backend"
        REPO_URL = "https://github.com/MatanItzhaki12/domain_monitoring_devops.git"
        CONTAINER_NAME = "temp_container_${BUILD_NUMBER}"
    }

    options { timestamps() }

    stages {
        stage('Checkout Backend Source') {
            steps {
                echo "Cloning backend branch from GitHub..."
                git branch: 'backend', url: "${REPO_URL}"
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

        stage('Build Backend Docker Image') {
            steps {
                echo "Building backend Docker image ${REGISTRY}/${IMAGE_NAME}:${env.TAG}"
                sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${env.TAG} ."
            }
        }

        stage('Run Backend API Tests') {
            steps {
                echo "Running backend API tests..."
                sh """
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d --name ${CONTAINER_NAME} ${REGISTRY}/${IMAGE_NAME}:${env.TAG}
                    docker exec ${CONTAINER_NAME} pytest tests/api_tests --maxfail=1 --disable-warnings -q
                """
            }
        }
        stage('Compute Semantic Version') {
            steps {
                script {
                    def latestDigest = sh(
                        script: '''
                        curl -s https://registry.hub.docker.com/v2/repositories/matan8520/dms_backend/tags?name=latest \
                        | jq -r '.results[0].digest'
                        ''',
                        returnStdout: true
                    ).trim()

                    def latestTag = sh(
                        script: '''
                        curl -s https://registry.hub.docker.com/v2/repositories/matan8520/dms_backend/tags?page_size=100 \
                        | jq -r --arg d ''' + latestDigest + ''' '
                            .results[]
                            | select(.digest == $d)
                            | select(.name | test("^v[0-9]+\\.[0-9]+\\.[0-9]+$"))
                            | .name
                        ' | head -1
                        ''',
                        returnStdout: true
                    ).trim()

                    if (!latestTag) {
                        latestTag = "v0.0.0"
                    }

                    def parts = latestTag.replace("v","").tokenize(".").collect { it.toInteger() }
                    def nextVersion = "v${parts[0]}.${parts[1]}.${parts[2] + 1}"

                    env.NEW_TAG_VERSION = nextVersion
                    echo "New version: ${env.NEW_TAG_VERSION}"
                }
            }
        }


        stage('Push Backend Image') {
            when { expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' } }
            steps {               
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:${env.NEW_TAG_VERSION}
                        docker tag ${REGISTRY}/${IMAGE_NAME}:${env.TAG} \$DOCKER_USER/${IMAGE_NAME}:latest
                        docker push \$DOCKER_USER/${IMAGE_NAME}:${env.NEW_TAG_VERSION}
                        docker push \$DOCKER_USER/${IMAGE_NAME}:latest
                        docker logout
                    """
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