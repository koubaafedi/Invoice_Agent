pipeline {
    agent any

    environment {
        APP_PORT = "8501"
        DOCKER_IMAGE_NAME = "invoice-app"
        DOCKER_CONTAINER_NAME = "invoice-app-container"
    }

    stages {
        stage('verify docker is working') {
            steps {
                script {
                    echo "Verifying Docker is working..."
                    sh "docker --version"
                    sh "docker ps"
                }
            }
        }
        // stage('Build Docker Image') {
        //     steps {
        //         script {
        //             echo "Building Docker image..."
        //             def customImage = docker.build("${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}")
        //             customImage.tag("latest")
        //             echo "Docker image ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} (and latest) built."
        //         }
        //     }
        // }

        // stage('Deploy Application') {
        //     steps {
        //         script {
        //             echo "Deploying Docker container..."
        //             sh "docker stop ${DOCKER_CONTAINER_NAME} || true"
        //             sh "docker rm ${DOCKER_CONTAINER_NAME} || true"

        //             def runningContainer = docker.image("${DOCKER_IMAGE_NAME}:latest").run(
        //                 "-p ${APP_PORT}:8501 --name ${DOCKER_CONTAINER_NAME}"
        //             )
        //             echo "Docker container ${DOCKER_CONTAINER_NAME} started."

        //             sh "sleep 10"
        //             sh "docker ps | grep ${DOCKER_CONTAINER_NAME}"
        //         }
        //     }
        // }

        // stage('Cleanup') {
        //     steps {
        //         script {
        //             echo "Cleaning up old Docker images..."
        //             sh """
        //             docker image prune -f
        //             docker images ${DOCKER_IMAGE_NAME} -q | sort -r | tail -n +4 | xargs docker rmi -f || true
        //             """
        //             echo "Cleanup complete."
        //         }
        //     }
        // }
    }

    // post {
    //     failure {
    //         script {
    //              echo "Pipeline failed, attempting to stop the container launched in this run..."
    //              sh "docker stop ${DOCKER_CONTAINER_NAME} || true"
    //              sh "docker rm ${DOCKER_CONTAINER_NAME} || true"
    //              echo "Container cleanup attempted."
    //         }
    //     }
    //     success {
    //          script {
    //              echo "Pipeline successful."
    //          }
    //     }
    // }
}