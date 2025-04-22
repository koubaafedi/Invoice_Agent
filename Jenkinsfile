pipeline {
    agent any // The main agent for checkout

    environment {
        // Replace with your Docker Hub username or private registry
        DOCKER_REGISTRY = "your_dockerhub_username"
        IMAGE_NAME = "invoice-assistant-app"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        APP_CONTAINER_NAME = "invoice_assistant_running"
        APP_PORT = "8501"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Application Docker Image') {
            agent {
                // Use a Docker container with the Docker CLI for this stage
                docker {
                    image 'docker:latest'
                    // Mount the workspace to access your code and Dockerfile
                    args '-v $PWD:$PWD -w $PWD' // Mount current workspace and set it as working directory
                    // Also mount the Docker socket from the host (via the Jenkins agent's mount)
                    args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                script {
                    // The docker command should now be available inside this agent container
                    sh "docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ."
                }
            }
        }

        stage('Test') {
             agent {
                // You could run tests in a container built from your app image
                // Or, if tests require the original code, use a Python image with workspace mounted
                docker {
                    image 'python:3.9-slim' // Example: use a Python image
                    args '-v $PWD:$PWD -w $PWD' // Mount current workspace
                }
            }
            steps {
                echo "Running tests (Implement actual test execution here)"
                // Install dependencies (within the ephemeral test container)
                sh 'pip install --no-cache-dir -r requirements.txt'
                // Run your tests
                // Example: sh 'pytest tests/'
            }
        }

        stage('Push Docker Image') {
             agent {
                // Use a Docker container with the Docker CLI for this stage
                docker {
                    image 'docker:latest'
                     args '-v /var/run/docker.sock:/var/run/docker.sock'
                     // Mount docker config for authentication if pushing to private/authenticated registry
                     // You might need to experiment with the path for Windows
                     // args '-v "%USERPROFILE%/.docker/config.json":/root/.docker/config.json:ro'
                }
            }
            steps {
                script {
                    // Push the image to the registry
                    // Replace 'dockerhub-credentials-id' with your Jenkins credential ID for your Docker registry
                    // The docker.withRegistry block handles authentication using the mounted config
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'dockerhub-credentials-id') {
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}").push()
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:latest").push()
                    }
                }
            }
        }

        stage('Deploy') {
             agent {
                // Use a Docker container with the Docker CLI for this stage
                docker {
                    image 'docker:latest'
                     args '-v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                echo "Stopping old container and starting new one..."
                // Stop and remove the old container instance of your application
                sh "docker stop ${APP_CONTAINER_NAME} || true"
                sh "docker rm ${APP_CONTAINER_NAME} || true"

                // Run a new container using the freshly built and pushed application image
                // Mount the Jenkins home volume if your app needs access to it (e.g., chat history file)
                sh """
                docker run -d \
                --name ${APP_CONTAINER_NAME} \
                -p ${APP_PORT}:${APP_PORT} \
                -v jenkins_home:/var/jenkins_home \
                ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                """ // Adjust volume mapping (-v) if needed
            }
        }
    }

    post {
        always {
            deleteDir()
        }
        failure {
            echo "Pipeline failed! Check the logs for details."
        }
        success {
            echo "Pipeline completed successfully! New application container is running."
        }
    }
}