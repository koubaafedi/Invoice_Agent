pipeline {
    agent any 

    environment {
        APP_PORT = "8501"
        APP_PROCESS_NAME = "streamlit run app.py"
        VENV_PATH = "${WORKSPACE}/venv"
        DAEMON_SCRIPT = "${WORKSPACE}/daemon.sh"
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
                echo "Creating daemon script for persistent application..."
                
                // Create a daemon script that will keep the app running
                sh """
                cat > ${DAEMON_SCRIPT} << 'EOL'
#!/bin/bash

# Configuration
WORKSPACE="${WORKSPACE}"
VENV="${VENV_PATH}"
PORT="${APP_PORT}"
LOGFILE="${WORKSPACE}/streamlit.log"
PIDFILE="${WORKSPACE}/app.pid"
STARTCMD="${VENV_PATH}/bin/python -m streamlit run app.py --server.port=${APP_PORT} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false"

# Function to start the application
start_app() {
    echo "[$(date)] Starting Streamlit app..." >> "\$LOGFILE"
    cd "${WORKSPACE}/src"
    nohup \$STARTCMD >> "\$LOGFILE" 2>&1 &
    echo \$! > "\$PIDFILE"
    echo "[$(date)] App started with PID \$(cat \$PIDFILE)" >> "\$LOGFILE"
}

# Function to check if app is running
is_running() {
    [ -f "\$PIDFILE" ] && ps -p \$(cat "\$PIDFILE") > /dev/null 2>&1
}

# Function to stop the application
stop_app() {
    if [ -f "\$PIDFILE" ]; then
        echo "[$(date)] Stopping Streamlit app..." >> "\$LOGFILE"
        PID=\$(cat "\$PIDFILE")
        kill \$PID 2>/dev/null || kill -9 \$PID 2>/dev/null || true
        rm -f "\$PIDFILE"
        echo "[$(date)] App stopped" >> "\$LOGFILE"
    fi
}

# Main logic
case "\$1" in
    start)
        if is_running; then
            echo "App already running with PID \$(cat \$PIDFILE)"
        else
            start_app
            sleep 5
            if is_running; then
                echo "App started successfully"
            else
                echo "Failed to start app, check logs"
                exit 1
            fi
        fi
        ;;
    stop)
        if is_running; then
            stop_app
            echo "App stopped"
        else
            echo "App not running"
        fi
        ;;
    restart)
        stop_app
        sleep 2
        start_app
        sleep 5
        if is_running; then
            echo "App restarted successfully"
        else
            echo "Failed to restart app, check logs"
            exit 1
        fi
        ;;
    status)
        if is_running; then
            echo "App is running with PID \$(cat \$PIDFILE)"
        else
            echo "App is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
EOL
                chmod +x ${DAEMON_SCRIPT}
                """
                
                // Stop any existing instances and start the app
                sh """
                # Stop any running instances
                pkill -f '${APP_PROCESS_NAME}' || true
                
                # Start the app using the daemon script
                ${DAEMON_SCRIPT} start
                
                # Wait for the app to initialize
                sleep 15
                
                # Check if app is running
                ${DAEMON_SCRIPT} status
                """
                
                // Verify the application is accessible
                sh """
                # Test app accessibility
                if curl -s --head --fail http://localhost:${APP_PORT} > /dev/null; then
                    echo "Application is accessible at http://localhost:${APP_PORT}"
                else
                    echo "ERROR: Application is not accessible!"
                    tail -n 50 ${WORKSPACE}/streamlit.log
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
            echo "Application successfully deployed!"
            echo "Access the application at: http://localhost:${APP_PORT}"
            echo ""
            echo "Use the following commands to manage the application:"
            echo "${DAEMON_SCRIPT} status  - Check if app is running"
            echo "${DAEMON_SCRIPT} restart - Restart the app"
            echo "${DAEMON_SCRIPT} stop    - Stop the app"
            echo ""
            echo "Set up a cron job to ensure app stays running:"
            echo "* * * * * ${DAEMON_SCRIPT} start >/dev/null 2>&1"
        }
    }
}