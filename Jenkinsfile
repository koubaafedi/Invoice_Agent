pipeline {
    agent any
    
    stages {
        stage('Setup Environment') {
            steps {
                sh 'python -m venv venv'
                sh '. venv/bin/activate && python -m pip install --upgrade pip'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'pkill -f streamlit || true'
                
                sh '''
                    . venv/bin/activate
                    nohup streamlit run app.py --server.port=8501 > streamlit.log 2>&1 &
                '''
                echo 'Streamlit app started on port 8501'

                sh "sleep 1000"
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
