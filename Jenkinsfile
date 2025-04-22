pipeline {
    agent any // Run on the default Jenkins agent (your Jenkins Docker container)

    environment {
        APP_PORT = "8501"
        // Define the process identifier here at the top level
        // Update the string to match how the process will appear with 'python3'
        APP_PROCESS_IDENTIFIER = "python3 -m streamlit run app.py"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from SCM..."
                checkout scm
                echo "Code checked out."
            }
        }

        stage('Setup Application Environment') {
            steps {
                echo "Setting up Python environment and installing dependencies..."
                // Use 'python3' here
                sh "python3 -m pip install --upgrade pip"
                sh "python3 -m pip install -r requirements.txt"
                echo "Dependencies installed."
            }
        }

        stage('Run Application') {
            steps {
                echo "Stopping existing application instance..."
                // Use the variable defined in the environment block
                sh "pkill -f '${APP_PROCESS_IDENTIFIER}' || true"
                echo "Existing instances stopped."

                echo "Launching application in background..."
                // Use 'python3' here
                sh """
                cd src
                nohup python3 -m streamlit run app.py \\
                    --server.port=${APP_PORT} \\
                    --server.address=0.0.0.0 \\
                    --server.enableCORS=false \\
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 &
                """
                echo "Application launch command executed."

                echo "Giving application time to start..."
                sh "sleep 15" // Wait for 15 seconds to allow the app to start

                echo "Verifying application process is running..."
                // Use the variable defined in the environment block
                sh "pgrep -f '${APP_PROCESS_IDENTIFIER}'"
                echo "Application process found."
            }
        }

        stage('Verify Application Access') {
            steps {
                 echo "Attempting to access application endpoint..."
                 sh "curl -Is http://localhost:${APP_PORT} | head -n 1"
                 echo "Application endpoint check completed."
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
            echo "Pipeline completed successfully! Application should be running in the background."
            echo "Access the app at http://localhost:${APP_PORT}"
        }
    }
}