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
                
                sh "sleep 20"
            }
        }
    }
}