pipeline {
    agent any // This agent will be used for checking out code and orchestrating Docker commands

    environment {
        // Replace with your Docker Hub username or private registry
        DOCKER_REGISTRY = "your_dockerhub_username"
        IMAGE_NAME = "invoice-assistant-app" // Give your application image a distinct name
        IMAGE_TAG = "${env.BUILD_NUMBER}" // Use Jenkins build number as tag
        APP_CONTAINER_NAME = "invoice_assistant_running" // Name for the running application container
        APP_PORT = "8501" // Port your Streamlit app runs on
    }

    stages {
        stage('Checkout') {
            steps {
                // Use checkout scm to get the code from your configured SCM
                checkout scm
            }
        }

        stage('Build Application Docker Image') {
            steps {
                script {
                    // Build the Docker image using the Dockerfile in your project root
                    // The Dockerfile will handle installing Python and dependencies
                    docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}", ".")
                }
            }
        }

        stage('Test') {
            steps {
                // This stage is optional but highly recommended.
                // You can run tests INSIDE a container built from your application image
                echo "Running tests (Implement actual test execution here)"
                // Example: Run a test command inside a container based on the new image
                // sh "docker run --rm ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} python -m unittest discover tests"
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    // Push the image to the registry
                    // Replace 'dockerhub-credentials-id' with your Jenkins credential ID for your Docker registry
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'dockerhub-credentials-id') {
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}").push()
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:latest").push() // Also push with 'latest' tag for convenience
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Stopping old container and starting new one..."
                // Stop and remove the old container instance of your application
                sh "docker stop ${APP_CONTAINER_NAME} || true" // Use || true to avoid failure if container doesn't exist
                sh "docker rm ${APP_CONTAINER_NAME} || true"

                // Run a new container using the freshly built and pushed application image
                // Map the application port and mount the data volume if needed
                // Ensure your data volume mapping here aligns with where your app expects the data
                sh """
                docker run -d \
                --name ${APP_CONTAINER_NAME} \
                -p ${APP_PORT}:${APP_PORT} \
                -v jenkins_home:/var/jenkins_home \
                ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                """ // Adjust volume mapping (-v) if your data is stored differently

                echo "Application deployment attempted. Check container logs for status."
                echo "Access the app at http://localhost:${APP_PORT}"
            }
        }
    }

    post {
        always {
            // Clean up the workspace after the job finishes
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