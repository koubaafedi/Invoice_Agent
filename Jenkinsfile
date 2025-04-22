pipeline {
    agent any 

    environment {
        APP_PORT = "8501"
        APP_PROCESS_NAME = "streamlit run app.py"
        VENV_PATH = "${WORKSPACE}/venv"
    }

    stages {
        stage('Setup') {
            steps {
                echo "Creating virtual environment and installing dependencies..."
                sh """
                # Create virtual environment
                python3 -m venv ${VENV_PATH}
                
                # Install dependencies in the virtual environment
                ${VENV_PATH}/bin/pip install --upgrade pip
                ${VENV_PATH}/bin/pip install -r requirements.txt
                """
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Deploying streamlit application..."
                
                // Stop any running instances of the app
                sh "pkill -f '${APP_PROCESS_NAME}' || true"
                
                // Launch the application using the virtual environment
                sh """
                cd src
                nohup ${VENV_PATH}/bin/python -m streamlit run app.py \
                    --server.port=${APP_PORT} \
                    --server.address=0.0.0.0 \
                    --server.enableCORS=false \
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 & 
                echo \$! > ../app.pid
                """
                
                // Give the app a chance to start and verify it's running
                sh """
                # Wait for application to start
                sleep 120
                
                # Check if application is running
                if curl -s --head --fail http://localhost:${APP_PORT} > /dev/null; then
                    echo "Application is running correctly"
                else
                    # Check logs for errors
                    echo "=== Application failed to start, last 20 lines of log: ==="
                    tail -n 20 ../streamlit.log || true
                    exit 1
                fi
                """
            }
        }
    }

    post {
        failure {
            echo "Pipeline failed! Check logs for details."
            // Cleanup in case of failure
            sh "pkill -f '${APP_PROCESS_NAME}' || true"
        }
        success {
            echo "Application successfully deployed!"
            echo "Access the application at: http://localhost:${APP_PORT}"
            // Display information about the running process
            sh "ps -ef | grep '${APP_PROCESS_NAME}' | grep -v grep || true"
        }
    }
}