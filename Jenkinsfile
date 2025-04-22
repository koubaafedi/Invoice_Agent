pipeline {
    agent any // Run on the default Jenkins agent (your Jenkins Docker container)

    environment {
        APP_PORT = "8501"
        // Use a more specific process name for pkill/pgrep if possible
        // Adjust this based on how the 'streamlit run app.py' process appears in 'ps aux' output
        APP_PROCESS_IDENTIFIER = "streamlit run app.py"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from SCM..."
                checkout scm // Checks out the code from the repository configured in the job
                echo "Code checked out."
            }
        }

        stage('Setup Application Environment') {
            steps {
                echo "Setting up Python environment and installing dependencies..."
                // THESE COMMANDS REQUIRE 'python' AND 'pip' TO BE AVAILABLE
                // IN THE JENKINS AGENT CONTAINER'S PATH.
                sh "python -m pip install --upgrade pip"
                sh "pip install -r requirements.txt"
                echo "Dependencies installed."
            }
        }

        stage('Run Application') {
            steps {
                echo "Stopping existing application instance..."
                // Stop any running instances of the application using pkill
                // '|| true' ensures the step doesn't fail if no process is found
                sh "pkill -f '${APP_PROCESS_IDENTIFIER}' || true"
                echo "Existing instances stopped."

                echo "Launching application in background..."
                // Launch application in background using nohup
                // Redirect output to a log file in the workspace
                sh """
                cd src
                nohup python -m streamlit run app.py \\
                    --server.port=${APP_PORT} \\
                    --server.address=0.0.0.0 \\
                    --server.enableCORS=false \\
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 &
                """
                echo "Application launch command executed."

                echo "Giving application time to start..."
                sh "sleep 15" // Wait for 15 seconds to allow the app to start

                echo "Verifying application process is running..."
                // Check if the process is running using pgrep
                sh "pgrep -f '${APP_PROCESS_IDENTIFIER}'"
                echo "Application process found."
            }
        }

        stage('Verify Application Access') {
            steps {
                 echo "Attempting to access application endpoint..."
                 // Perform a basic health check by trying to access the application's HTTP endpoint
                 // Requires 'curl' or 'wget' to be available in the Jenkins agent container
                 sh "curl -Is http://localhost:${APP_PORT} | head -n 1"
                 echo "Application endpoint check completed."
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
            echo "Pipeline completed successfully! Application should be running in the background."
            echo "Access the app at http://localhost:${APP_PORT}"
        }
    }
}