pipeline {
    agent any

    triggers { 
        githubPush() 
    }

    environment {
        DOCKER_HUB = credentials('DockerHubCred')
        GITHUB_REPO_URL = 'https://github.com/anuja-jmk/Skill-Ex.git'
        EMAIL_TO = 'aieshah9241@gmail.com, 203ajmk@gmail.com'
        KUBECONFIG = "/var/lib/jenkins/kube-minikube/config"
        MINIKUBE_HOME = "/var/lib/jenkins/kube-minikube/.minikube"
        RAPIDAPI_KEY = credentials('rapidapi-key')
        ANSIBLE_ROLES_PATH = "${WORKSPACE}/ansible/roles"
    }

    options {
        // Stops Jenkins from checking out code before the cleanup step runs
        skipDefaultCheckout(true) 
    }
    
    stages {
        stage('Clean Workspace & Checkout SCM') {
            steps {
                sh 'git clean -fdx'
                sh 'git reset --hard HEAD'
                // Deletes the workspace directory before the build starts
                cleanWs()
                checkout scm
            }
        }

        stage('Detect Changes') {
            steps {
                script {
                    echo "Forcing all builds to run regardless of changes."
                    
                    env.INGESTION_CHANGED = 'true'
                    env.DASHBOARD_CHANGED = 'true'
                    env.ML_CHANGED = 'true'
                    env.MLFLOW_CHANGED = 'true'
                    env.ELK_CHANGED = 'true'
                    
                    echo "Flags set: Ingestion=${env.INGESTION_CHANGED}, Dashboard=${env.DASHBOARD_CHANGED}, ML=${env.ML_CHANGED}"
                }
            }
        }

        stage('Build & Push Ingestion') {
            when { expression { env.INGESTION_CHANGED == 'true' } }
            steps {
                script {
                    docker.withRegistry('', 'DockerHubCred') {
                        def img = docker.build("${DOCKER_HUB_USR}/microservices-ingestion:latest", "-f microservices/ingestion/Dockerfile microservices")
                        img.push()
                    }
                }
            }
        }

        stage('Build, Test & Push Dashboard') {
            when { expression { env.DASHBOARD_CHANGED == 'true' } }
            steps {
                script {
                    // 1. Build the dashboard image
                    docker.withRegistry('', 'DockerHubCred') {
                        docker.build("${DOCKER_HUB_USR}/microservices-dashboard:latest", "-f microservices/dashboard/Dockerfile microservices")
                    }
                    
                    // 2. Run unit tests in an isolated, temporary container shell
                    // Using --rm guarantees the container system clears itself automatically upon exit
                    sh """
                        echo "Running dashboard unit tests inside separate test container..."
                        docker run --rm ${DOCKER_HUB_USR}/microservices-dashboard:latest \
                        sh -c "cd microservices/dashboard && pip install pytest pytest-mock && pytest test_app.py"
                    """
                    
                    // 3. Push to registry (only reached if the docker run command returns exit code 0)
                    docker.withRegistry('', 'DockerHubCred') {
                        sh "docker push ${DOCKER_HUB_USR}/microservices-dashboard:latest"
                    }
                }
            }
        }

        stage('Build, Test & Push ML Services') {
            when { expression { env.ML_CHANGED == 'true' } }
            steps {
                script {
                    // 1. Build the ML images
                    docker.withRegistry('', 'DockerHubCred') {
                        docker.build("${DOCKER_HUB_USR}/microservices-ml-api:latest", "-f microservices/ml/Dockerfile microservices")
                        docker.build("${DOCKER_HUB_USR}/microservices-model-training:latest", "-f microservices/model_training/Dockerfile microservices")
                    }
                    
                    // 2. Run PII Masker unit tests inside the isolated ML API container
                    sh """
                        echo "Running ML API unit tests inside separate test container..."
                        docker run --rm ${DOCKER_HUB_USR}/microservices-ml-api:latest \
                        sh -c "cd microservices && pip install pytest && pytest tests/test_pii_masker.py"
                    """
                    
                    // 3. Push both stable images if tests pass
                    docker.withRegistry('', 'DockerHubCred') {
                        sh "docker push ${DOCKER_HUB_USR}/microservices-ml-api:latest"
                        sh "docker push ${DOCKER_HUB_USR}/microservices-model-training:latest"
                    }
                }
            }
        }

        stage('Build & Push MLflow') {
            when { expression { env.MLFLOW_CHANGED == 'true' } }
            steps {
                script {
                    docker.withRegistry('', 'DockerHubCred') {
                        def img = docker.build("${DOCKER_HUB_USR}/microservices-mlflow:latest", "microservices/mlflow")
                        img.push()
                    }
                }
            }
        }

        stage('Run Ansible Deployment') {
            steps {
                echo 'Triggering Ansible Playbook with Vault Decryption...'
        
                // Pull the vault password securely from Jenkins Credentials
                withCredentials([string(credentialsId: 'ANSIBLE_VAULT_PASSWORD', variable: 'VAULT_PASS')]) {
                    script {
                        // Write the password to a temporary file that Ansible can read
                        sh 'echo "$VAULT_PASS" > .vault_pass'
                        
                        // Run the playbook, passing the vault password file flag
                        sh '''
                            ansible-playbook -i ansible/inventory.ini ansible/deploy.yml \
                            --vault-password-file .vault_pass
                        '''
                        
                        // Clean up the password file immediately so it doesn't linger
                        sh 'rm -f .vault_pass'
                    }
                }
            }
        }
    }

    post {
        success {
            mail to: "${EMAIL_TO},203ajmk@gmail.com",
                 subject: "SUCCESS: Skill-Ex Build '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                 body: "Great news! The Skill-Ex microservices were successfully built and deployed.\n\nBuild URL: ${env.BUILD_URL}"
        }
        failure {
            mail to: "${EMAIL_TO},203ajmk@gmail.com",
                 subject: "FAILURE: Skill-Ex Build '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                 body: "Attention: The Skill-Ex build failed. Please check the logs immediately.\n\nBuild URL: ${env.BUILD_URL}"
        }
    }
}