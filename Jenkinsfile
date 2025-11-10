pipeline {
    agent { label 'Slave' }

    environment {
        REGISTRY = "symmetramain"
        IMAGE_NAME = "etcsys"
        TAG = "${env.BUILD_NUMBER}"
    }

    options {
        timestamps()
    }

    stages {

        stage('Checkout from GitHub') {
            steps {
                echo "Cloning GitHub repository..."
                git branch: 'main', url: 'https://github.com/cerform/domain_monitoring_devops.git'
            }
        }

        stage('Build Temporary Docker Image') {
            steps {
                echo "Building temporary Docker image..."
                sh '''
                docker build -t $REGISTRY/$IMAGE_NAME:$TAG .
                '''
            }
        }

        stage('Run Temporary Container') {
            steps {
                echo "Starting container for test execution..."
                sh '''
                docker run -d --name temp_container $REGISTRY/$IMAGE_NAME:$TAG tail -f /dev/null
                '''
            }
        }

        stage('Testing Suite') {
            parallel {
                stage('Selenium UI Tests') {
                    steps {
                        echo "Running Selenium tests..."
                        sh '''
                        docker exec temp_container pytest tests/selenium_tests --maxfail=1 --disable-warnings -q || exit 1
                        '''
                    }
                }
                stage('Pytest Backend Tests') {
                    steps {
                        echo "Running backend Pytest tests..."
                        sh '''
                        docker exec temp_container pytest tests/api_tests --maxfail=1 --disable-warnings -q || exit 1
                        '''
                    }
                }
            }
        }

        stage('Publish to DockerHub') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo "Pushing image to DockerHub..."
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker tag $REGISTRY/$IMAGE_NAME:$TAG $DOCKER_USER/$IMAGE_NAME:$TAG
                    docker push $DOCKER_USER/$IMAGE_NAME:$TAG
                    '''
                }
            }
        }

        stage('Cleanup') {
            steps {
                echo "Cleaning up temporary resources..."
                sh '''
                docker rm -f temp_container || true
                docker rmi $REGISTRY/$IMAGE_NAME:$TAG || true
                '''
            }
        }
    }

    post {
        success {
            echo "SUCCESS: All tests passed. Image pushed to DockerHub as $REGISTRY/$IMAGE_NAME:$TAG"
        }
        failure {
            echo "FAILURE: One or more stages failed. Check logs for details."
            sh '''
            echo "Collecting failure logs..."
            docker logs temp_container || true
            '''
        }
        always {
            echo "Generating report and cleaning workspace..."
            deleteDir()
        }
    }
}
