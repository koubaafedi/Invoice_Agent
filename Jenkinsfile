pipeline {
    agent any

    environment {
        APP_PORT = "8501"
        // APP_PROCESS_NAME is not directly used in this Docker-centric approach
        DOCKER_IMAGE_NAME = "invoice-app"
        DOCKER_CONTAINER_NAME = "invoice-app-container"
    }

    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image..."
                    // Use docker.build() provided by the Docker Pipeline plugin
                    // It looks for a Dockerfile in the current directory by default
                    // We tag the image with the build number
                    def customImage = docker.build("${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}")

                    // Optionally tag it as 'latest' as well
                    customImage.tag("latest")

                    echo "Docker image ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} (and latest) built."
                }
            }
        }

        stage('Deploy Application') {
            steps {
                script {
                    echo "Deploying Docker container..."

                    // Stop and remove any existing container using sh for simplicity
                    // The Docker Pipeline plugin's run method is better for managing
                    // containers created *by* the pipeline run, but stopping
                    // a potentially pre-existing container is cleaner with sh.
                    sh "docker stop ${DOCKER_CONTAINER_NAME} || true"
                    sh "docker rm ${DOCKER_CONTAINER_NAME} || true"

                    // Run the application in a Docker container using docker.image().run()
                    // This automatically runs in detached mode and can be assigned a name.
                    // We use the 'latest' tag for deployment
                    def runningContainer = docker.image("${DOCKER_IMAGE_NAME}:latest").run(
                        "-p ${APP_PORT}:8501 --name ${DOCKER_CONTAINER_NAME}"
                    )

                    echo "Docker container ${DOCKER_CONTAINER_NAME} started."

                    // Note: Verifying container running is often done by checking
                    // the application's health endpoint rather than docker ps
                    // but keeping the check you had:
                    sh "sleep 10" // Give the app time to start
                    sh "docker ps | grep ${DOCKER_CONTAINER_NAME}"

                    // The 'runningContainer' object can be used here if needed,
                    // e.g., runningContainer.id or runningContainer.stop() later
                    // in the post section for cleaner teardown of *this* specific run.
                    // However, the cleanup in the next stage handles general cleanup.
                }
            }
        }

        stage('Cleanup') {
            steps {
                script {
                    echo "Cleaning up old Docker images..."
                    // Keeping sh for general Docker system prune and old image removal
                    // as this is outside the scope of a specific container run by the plugin.
                    sh """
                    docker image prune -f
                    docker images ${DOCKER_IMAGE_NAME} -q | sort -r | tail -n +4 | xargs docker rmi -f || true
                    """
                    echo "Cleanup complete."
                }
            }
        }
    }

    // Using the post section to ensure the container from *this* run is stopped on failure
    post {
        failure {
            script {
                 echo "Pipeline failed, attempting to stop the container launched in this run..."
                 // Find the container by name and stop/remove it on failure
                 // Use sh as the 'runningContainer' object might not be available in post/failure
                 sh "docker stop ${DOCKER_CONTAINER_NAME} || true"
                 sh "docker rm ${DOCKER_CONTAINER_NAME} || true"
                 echo "Container cleanup attempted."
            }
        }
        success {
             script {
                 echo "Pipeline successful."
                 // You might choose to stop the container here on success too,
                 // depending on your deployment strategy.
                 // sh "docker stop ${DOCKER_CONTAINER_NAME} || true"
                 // sh "docker rm ${DOCKER_CONTAINER_NAME} || true"
             }
        }
    }
}