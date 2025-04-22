pipeline {
    agent any
    
    environment {
        APP_NAME = "jenkins_invoice_assistant"
        DOCKER_PORT = "8501"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                sh "docker build -t ${APP_NAME} ."
            }
        }
        
        stage('Deploy') {
            steps {
                // Remove existing container if it exists
                sh "docker rm -f ${APP_NAME} || true"
                
                // Run the new container
                sh "docker run -d -p ${DOCKER_PORT}:8501 --name ${APP_NAME} -v ${WORKSPACE}/data:/app/data -v ${WORKSPACE}/secrets:/app/secrets ${APP_NAME}"
                
                echo "Application deployed at http://localhost:${DOCKER_PORT}"
            }
        }
    }
    
    post {
        failure {
            echo "Pipeline failed! Check the logs for details."
        }
        success {
            echo "Pipeline completed successfully!"
        }
    }
}