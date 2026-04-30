pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                // This "binds" your secret file to a temporary variable (envFile)
                withCredentials([file(credentialsId: 'discord-terminal-bot-env', variable: 'envFile')]) {
                    script {
                        sh "cp ${envFile} .env"
                        
                        // 2. Run docker compose (it will automatically pick up the .env file)
                        sh "docker compose up -d --build"
                        
                        // 3. Clean up the .env file after deployment (optional but safer)
                        sh "rm .env"
                    }
                }
            }
        }
    }
    post {
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed. Check the logs.'
        }
    }
}
