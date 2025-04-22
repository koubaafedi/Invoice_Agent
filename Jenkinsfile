pipeline {
    agent any 

    environment {
        APP_PORT = "8501"
        APP_PROCESS_NAME = "streamlit run app.py"
        DOCKER_IMAGE_NAME = "invoice-app"
        DOCKER_CONTAINER_NAME = "invoice-app-container"
    }

    stages {
        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh """
                # Build the Docker image using the external Dockerfile
                docker build -t ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} .
                docker tag ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} ${DOCKER_IMAGE_NAME}:latest
                """
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Deploying Docker container..."
                
                // Stop and remove any existing container
                sh """
                docker stop ${DOCKER_CONTAINER_NAME} || true
                docker rm ${DOCKER_CONTAINER_NAME} || true
                """
                
                // Run the application in a Docker container
                sh """
                docker run -d \
                    --name ${DOCKER_CONTAINER_NAME} \
                    -p ${APP_PORT}:8501 \
                    ${DOCKER_IMAGE_NAME}:latest
                """
                
                sh "sleep 10"
                
                // Verify container is running
                sh "docker ps | grep ${DOCKER_CONTAINER_NAME}"
            }
        }
        
        stage('Cleanup') {
            steps {
                echo "Cleaning up old Docker images..."
                // Keep only the latest 3 images
                sh """
                docker image prune -f
                docker images ${DOCKER_IMAGE_NAME} -q | sort -r | tail -n +4 | xargs docker rmi -f || true
                """
            }
        }
    }
    
    post {
        failure {
            echo "Pipeline failed, ensuring container is cleaned up..."
            sh "docker stop ${DOCKER_CONTAINER_NAME} || true"
            sh "docker rm ${DOCKER_CONTAINER_NAME} || true"
        }
    }
}