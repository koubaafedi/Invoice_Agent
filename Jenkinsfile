pipeline {
    agent any 

    environment {
        DOCKER_REGISTRY = "koubaafedi"
        IMAGE_NAME = "assistant-facture"
        IMAGE_TAG = env.BUILD_NUMBER
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/koubaafedi/Invoice_Agent'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}", ".")
                }
            }
        }

        stage('Test') {
            steps {
                // Assuming you have a requirements.txt
                sh 'pip install -r requirements.txt'
                // Add commands to run your tests
                // Example: sh 'pytest tests/'
                sh 'echo "Running tests (replace with actual test command)"'
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    // Push the image to the registry
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'dockerhub-credentials-id') { // Replace 'dockerhub-credentials-id' with your Jenkins credential ID for Docker Hub
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}").push()
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:latest").push() // Also push with 'latest' tag
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Stopping old container and starting new one..."
                // Stop the old container
                sh "docker stop jenkins_invoice_assistant || true" // Use || true to avoid failure if container doesn't exist
                // Remove the old container
                sh "docker rm jenkins_invoice_assistant || true"
                // Run the new container
                sh "docker run -d --name jenkins_invoice_assistant -p 8501:8501 -v jenkins_home:/var/jenkins_home ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" // Adjust ports and volume as needed. Streamlit default is 8501.
                echo "Deployment complete. Access the app at http://localhost:8501"
            }
        }
    }
}