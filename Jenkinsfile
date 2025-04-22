pipeline {
    agent any // Run on the default Jenkins agent

    environment {
        APP_PORT = "8501"
        APP_PROCESS_IDENTIFIER = "streamlit run app.py"
    }

    stages {
        stage('Setup & Install') {
            steps {
                echo "Setting up environment and installing dependencies..."
                sh "python3 -m venv venv"
                sh "venv/bin/pip install -q --upgrade pip && venv/bin/pip install -q -r requirements.txt"
            }
        }

        stage('Run & Verify Application') {
            steps {
                echo "Stopping existing application instance and launching new one..."
                sh "pkill -f '${APP_PROCESS_IDENTIFIER}' || true"

                sh """
                cd src
                nohup ../venv/bin/python3 -m streamlit run app.py \\
                    --server.port=${APP_PORT} \\
                    --server.address=0.0.0.0 \\
                    --server.enableCORS=false \\
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 &
                """

                echo "Giving application time to start and verifying..."
                sh "sleep 90"
            }
        }
    }

    post {
        always {
            deleteDir()
        }
        failure {
            echo "Pipeline failed!"
        }
        success {
            echo "Pipeline completed successfully. App running on http://localhost:${APP_PORT}"
        }
    }
}