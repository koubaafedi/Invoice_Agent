pipeline {
    agent any 

    environment {
        APP_PORT = "8501"
        APP_PROCESS_IDENTIFIER = "venv/bin/python3 -m streamlit run app.py"
    }

    stages {

        stage('Setup & Install') {
            steps {
                echo "Setting up environment and installing dependencies..."
                sh "python3 -m venv venv"
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

                sh "sleep 55"
            }
        }
    }

    post {
        failure {
            echo "Pipeline failed!"
        }
        success {
            echo "Pipeline completed successfully. App running on http://localhost:${APP_PORT}"
        }
    }
}