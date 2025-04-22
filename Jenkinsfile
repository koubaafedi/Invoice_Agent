pipeline {
    agent any // Run on the default Jenkins agent

    environment {
        APP_PORT = "8501"
        // Define the process identifier here
        APP_PROCESS_IDENTIFIER = "venv/bin/python3 -m streamlit run app.py"
    }

    stages {
        // The Declarative pipeline automatically performs an initial checkout,
        // so a dedicated 'Checkout' stage is often redundant unless you need
        // to checkout multiple repositories or at a different point.

        stage('Setup & Install') {
            steps {
                echo "Setting up environment and installing dependencies..."
                // Create a virtual environment
                sh "python3 -m venv venv"
                // Install dependencies into the virtual environment
                sh "venv/bin/pip install --upgrade pip && venv/bin/pip install -r requirements.txt"
            }
        }

        stage('Run & Verify Application') {
            steps {
                echo "Stopping existing application instance and launching new one..."
                // Stop any running instances
                sh "pkill -f '${APP_PROCESS_IDENTIFIER}' || true"

                // Launch application in background from virtual environment
                sh """
                cd src
                nohup ../venv/bin/python3 -m streamlit run app.py \\
                    --server.port=${APP_PORT} \\
                    --server.address=0.0.0.0 \\
                    --server.enableCORS=false \\
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 &
                """

                echo "Giving application time to start and verifying..."
                // Give it time to start and check if the process is running
                sh "sleep 15 && pgrep -f '${APP_PROCESS_IDENTIFIER}'"

                // Verify application access
                sh "curl -Is http://localhost:${APP_PORT} | head -n 1"
            }
        }
    }

    post {
        always {
            deleteDir() // Clean up the workspace after the job finishes
        }
        failure {
            echo "Pipeline failed!"
        }
        success {
            echo "Pipeline completed successfully. App running on http://localhost:${APP_PORT}"
        }
    }
}