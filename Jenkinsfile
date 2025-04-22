pipeline {
    agent any 

    environment {
        APP_PORT = "8501"
        APP_PROCESS_NAME = "streamlit run app.py"
    }

    stages {
        stage('Setup') {
            steps {
                echo "Installing dependencies..."
                sh "pip install --user -r requirements.txt"
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Deploying streamlit application..."
                
                // Stop any running instances of the app
                sh "pkill -f '${APP_PROCESS_NAME}' || true"
                
                // Launch the application properly so it persists
                sh """
                cd src
                nohup python3 -m streamlit run app.py \
                    --server.port=${APP_PORT} \
                    --server.address=0.0.0.0 \
                    --server.enableCORS=false \
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 & 
                echo \$! > ../app.pid
                """
                
                // Give the app a moment to start
                sh "sleep 10"
                
                // Verify the application is running
                sh """
                if curl -s http://localhost:${APP_PORT} > /dev/null; then
                    echo "Application is running correctly"
                else
                    echo "Application failed to start properly"
                    exit 1
                fi
                """
            }
        }
    }

    post {
        failure {
            echo "Pipeline failed! Check logs for details."
        }
        success {
            echo "Application successfully deployed and verified!"
            echo "Access the application at: http://localhost:${APP_PORT}"
        }
    }
}