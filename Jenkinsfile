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
                # Create virtual environment if it doesn't exist
                [ ! -d ${VENV_PATH} ] && python3 -m venv ${VENV_PATH}
                
                # Install dependencies quietly
                ${VENV_PATH}/bin/pip install -q --upgrade pip
                ${VENV_PATH}/bin/pip install -q -r requirements.txt
                """
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Deploying streamlit application..."
                
                // Stop any running instances of the app
                sh "pkill -f '${APP_PROCESS_NAME}' || true"
                
                // Create a startup script that will be used to launch the app
                sh """
                cat > ${WORKSPACE}/start_app.sh << 'EOL'
#!/bin/bash
cd ${WORKSPACE}/src
nohup ${VENV_PATH}/bin/python -m streamlit run app.py \\
    --server.port=${APP_PORT} \\
    --server.address=0.0.0.0 \\
    --server.enableCORS=false \\
    --server.enableXsrfProtection=false > ${WORKSPACE}/streamlit.log 2>&1 &
echo \$! > ${WORKSPACE}/app.pid
EOL

                chmod +x ${WORKSPACE}/start_app.sh
                
                # Run the startup script and detach it from Jenkins process tree
                ${WORKSPACE}/start_app.sh
                """
                
                // Give the app a moment to start
                sh "sleep 10"
                
                // Verify the application is running
                sh """
                if curl -s --head --fail http://localhost:${APP_PORT} > /dev/null; then
                    echo "Application is running correctly"
                else
                    echo "Application failed to start properly"
                    cat ${WORKSPACE}/streamlit.log
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
            
            // Create a simple health check script that can be run as a cron job
            sh """
            cat > ${WORKSPACE}/health_check.sh << 'EOL'
#!/bin/bash
if ! pgrep -f "${APP_PROCESS_NAME}" > /dev/null; then
    echo "Streamlit app is not running. Restarting..."
    ${WORKSPACE}/start_app.sh
    echo "App restarted at \$(date)" >> ${WORKSPACE}/restart_log.txt
fi
EOL
            chmod +x ${WORKSPACE}/health_check.sh
            
            echo "Created health check script at ${WORKSPACE}/health_check.sh"
            echo "Consider adding this to crontab to ensure app stays running:"
            echo "*/5 * * * * ${WORKSPACE}/health_check.sh"
            """
            
            // Display information about the running process
            sh "ps -ef | grep '${APP_PROCESS_NAME}' | grep -v grep || true"
        }
    }
}