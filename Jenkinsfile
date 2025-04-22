pipeline {
    agent any
    
    environment {
        PORT = "8501"
        APP_PROCESS_NAME = "jenkins_invoice_assistant"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                // Create and activate virtual environment if needed
                sh "python -m pip install --upgrade pip"
                sh "pip install -r requirements.txt"
            }
        }
        
        stage('Run Application') {
            steps {
                // Stop existing application instance if running
                sh "pkill -f 'streamlit run app.py' || true"
                
                // Launch application in background with nohup to keep it running after Jenkins job completes
                sh """
                cd src
                nohup python -m streamlit run app.py \
                    --server.port=${PORT} \
                    --server.address=0.0.0.0 \
                    --server.enableCORS=false \
                    --server.enableXsrfProtection=false > ../streamlit.log 2>&1 &
                """
                
                // Give it time to start
                sh "sleep 5"
                
                echo "Application started at http://localhost:${PORT}"
                echo "Check logs in ${WORKSPACE}/streamlit.log"
                
                // Verify it's running
                sh "ps aux | grep 'streamlit run app.py' | grep -v grep"
            }
        }
    }
    
    post {
        failure {
            echo "Pipeline failed! Check the logs for details."
        }
        success {
            echo "Pipeline completed successfully! Application is running in background."
        }
    }
}