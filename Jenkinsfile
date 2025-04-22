pipeline {
    agent any 

    environment {
        APP_PORT = "8501"
        APP_PROCESS_NAME = "streamlit run app.py"
        VENV_PATH = "${WORKSPACE}/venv"
        SERVICE_FILE = "${WORKSPACE}/streamlit.service"
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
                ${VENV_PATH}/bin/pip install -q google-generativeai --upgrade
                """
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Setting up systemd service for the application..."
                
                // Create a systemd service file
                sh """
                cat > ${SERVICE_FILE} << 'EOL'
[Unit]
Description=Streamlit Invoice Assistant
After=network.target

[Service]
User=jenkins
WorkingDirectory=${WORKSPACE}/src
ExecStart=${VENV_PATH}/bin/python -m streamlit run app.py --server.port=${APP_PORT} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
Restart=always
RestartSec=5
StandardOutput=append:${WORKSPACE}/streamlit.log
StandardError=append:${WORKSPACE}/streamlit.log

[Install]
WantedBy=multi-user.target
EOL
                """
                
                // Install and start the service
                sh """
                # Move service file to system directory
                sudo cp ${SERVICE_FILE} /etc/systemd/system/streamlit.service
                
                # Reload systemd to recognize the new service
                sudo systemctl daemon-reload
                
                # Stop any existing service and start the new one
                sudo systemctl stop streamlit.service || true
                sudo systemctl enable streamlit.service
                sudo systemctl start streamlit.service
                
                # Wait for the service to start
                sleep 10
                
                # Check service status
                sudo systemctl status streamlit.service
                """
                
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
        }
        success {
            echo "Application successfully deployed as a system service!"
            echo "Access the application at: http://localhost:${APP_PORT}"
            echo "Service will automatically restart if it crashes."
            echo "To check service status: sudo systemctl status streamlit.service"
            echo "To view logs: sudo journalctl -u streamlit.service"
        }
    }
}