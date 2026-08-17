// Jenkins pipeline variant (for agencies running Jenkins on-prem).
pipeline {
    agent any

    environment {
        IMAGE_TAG = "${env.GIT_COMMIT.take(8)}"
        ECR_REGISTRY = credentials('ecr-registry')
    }

    stages {
        stage('Test') {
            steps {
                sh '''
                    pip install -r CORE_AGENT_INFRASTRUCTURE/frameworks/langchain_setup/requirements.txt
                    pip install ruff pytest
                    ruff check CORE_AGENT_INFRASTRUCTURE VERTICALS
                    pytest tests/ -q
                '''
            }
        }
        stage('Build & Push') {
            steps {
                sh '''
                    docker build -f DEPLOYMENT_INFRASTRUCTURE/docker/Dockerfile.agent-core \
                        -t ${ECR_REGISTRY}/agent-core:${IMAGE_TAG} .
                    docker push ${ECR_REGISTRY}/agent-core:${IMAGE_TAG}
                '''
            }
        }
        stage('Deploy Staging') {
            when { branch 'develop' }
            steps {
                sh '''
                    kubectl set image deployment/agent-core \
                        agent-core=${ECR_REGISTRY}/agent-core:${IMAGE_TAG} -n stratum
                    kubectl rollout status deployment/agent-core -n stratum --timeout=5m
                '''
            }
        }
    }
    post {
        failure {
            slackSend color: 'danger', message: "Stratum pipeline FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
