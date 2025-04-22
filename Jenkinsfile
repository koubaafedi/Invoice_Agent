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
                echo "Setting up Python virtual environment and installing dependencies..."
                // Create a virtual environment named 'venv' in the workspace
                sh "python3 -m venv venv"

                // Install dependencies into the virtual environment
                // Use the pip executable from the virtual environment
                sh "venv/bin/pip install --upgrade pip"
                sh "venv/bin/pip install -r requirements.txt"

                echo "Dependencies installed in virtual environment."
            }
        }

        stage('Run Application') {
            steps {
                echo "Stopping existing application instance..."
                // The process identifier will now be the path to the venv python3
                // Adjust this based on how the process appears, maybe "venv/bin/python3 -m streamlit..."
                APP_PROCESS_IDENTIFIER = "venv/bin/python3 -m streamlit run app.py" // Update identifier

                // Stop any running instances
                sh "pkill -f '${APP_PROCESS_IDENTIFIER}' || true"
                echo "Existing instances stopped."

                echo "Launching application in background from virtual environment..."
                // Run the application using the python3 executable from the virtual environment
                sh """
                cd src
                nohup ../venv/bin/python3 -m streamlit run app.py \\
                    --server.port=${APP_PORT} \\
                    --server.address=0.0.0.0 \\
                    --server.enableCORS=false \\
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 &
                """
                echo "Application launch command executed."

                echo "Giving application time to start..."
                sh "sleep 15"

                echo "Verifying application process is running..."
                // Check for the process using the virtual environment path
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