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
                // Change 'python' to 'python3'
                sh "python3 -m pip install --upgrade pip"
                sh "python3 -m pip install -r requirements.txt" // Use python3 with pip
                echo "Dependencies installed."
            }
        }

        stage('Run Application') {
            steps {
                echo "Stopping existing application instance..."
                // Use a more specific process name for pkill/pgrep if possible
                // Adjust this based on how the 'streamlit run app.py' process appears in 'ps aux' output
                // The process will now likely show 'python3 -m streamlit...'
                APP_PROCESS_IDENTIFIER = "python3 -m streamlit run app.py" // Update identifier if needed
                sh "pkill -f '${APP_PROCESS_IDENTIFIER}' || true"
                echo "Existing instances stopped."

                echo "Launching application in background..."
                // Change 'python' to 'python3'
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
                // Change 'python' to 'python3' in pgrep if you updated the identifier
                sh "pgrep -f '${APP_PROCESS_IDENTIFIER}'" // Or adjust if pgrep target needs updating
                echo "Application process found."
            }
        }

        stage('Verify Application Access') {
            steps {
                 echo "Attempting to access application endpoint..."
                 // curl was confirmed to be installed
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