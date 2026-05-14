pipeline {
    agent any

    triggers { 
        githubPush() 
    }

    environment {
        DOCKER_USER_NAME = 'anujajose'
        GITHUB_REPO_URL = 'https://github.com/anuja-jmk/Skill-Ex.git'
        EMAIL_TO = 'anuja2033@gmail.com'
        // Change Detection Flags
        INGESTION_CHANGED = 'false'
        DASHBOARD_CHANGED = 'false'
        ML_CHANGED = 'false'
        MLFLOW_CHANGED = 'false'
        ELK_CHANGED = 'false'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: "${GITHUB_REPO_URL}"
            }
        }

        stage('Detect Changes') {
            steps {
                script {
                    def commits = sh(script: "git rev-list HEAD --count", returnStdout: true).trim().toInteger()

                    if (commits < 2) {
                        echo "First commit or fresh repo detected. Forcing all builds."
                        env.INGESTION_CHANGED = 'true'
                        env.DASHBOARD_CHANGED = 'true'
                        env.ML_CHANGED = 'true'
                        env.MLFLOW_CHANGED = 'true'
                        env.ELK_CHANGED = 'true'
                    } else {
                        def changeLog = sh(script: "git diff --name-only HEAD~1 HEAD", returnStdout: true).trim().split("\n")
                        
                        env.INGESTION_CHANGED = changeLog.any { it.startsWith("microservices/ingestion/") || it.startsWith("microservices/shared/") }.toString()
                        env.DASHBOARD_CHANGED = changeLog.any { it.startsWith("microservices/dashboard/") || it.startsWith("microservices/shared/") }.toString()
                        env.ML_CHANGED = changeLog.any { it.startsWith("microservices/ml/") || it.startsWith("microservices/model_training/") || it.startsWith("microservices/shared/") }.toString()
                        env.MLFLOW_CHANGED = changeLog.any { it.startsWith("microservices/mlflow/") }.toString()
                        env.ELK_CHANGED = changeLog.any { it.startsWith("elk/") }.toString()
                    }
                }
            }
        }

        stage('Build & Push Ingestion') {
            when { expression { env.INGESTION_CHANGED == 'true' } }
            steps {
                script {
                    docker.withRegistry('', 'DockerCred') {
                        def img = docker.build("${DOCKER_USER_NAME}/microservices-ingestion", "-f microservices/ingestion/Dockerfile microservices")
                        img.push('latest')
                    }
                }
            }
        }

        // stage('Build & Push Dashboard') {
        //     when { expression { env.DASHBOARD_CHANGED == 'true' } }
        //     steps {
        //         script {
        //             docker.withRegistry('', 'DockerCred') {
        //                 def img = docker.build("${DOCKER_USER_NAME}/microservices-dashboard", "-f microservices/dashboard/Dockerfile microservices")
        //                 img.push('latest')
        //             }
        //         }
        //     }
        // }

        stage('Build & Push ML Services') {
            when { expression { env.ML_CHANGED == 'true' } }
            steps {
                script {
                    docker.withRegistry('', 'DockerCred') {
                        def mlApi = docker.build("${DOCKER_USER_NAME}/microservices-ml-api", "-f microservices/ml/Dockerfile microservices")
                        mlApi.push('latest')
                        
                        def training = docker.build("${DOCKER_USER_NAME}/microservices-model-training", "-f microservices/model_training/Dockerfile microservices")
                        training.push('latest')
                    }
                }
            }
        }

        stage('Build & Push MLflow') {
            when { expression { env.MLFLOW_CHANGED == 'true' } }
            steps {
                script {
                    docker.withRegistry('', 'DockerCred') {
                        // Custom MLflow build from the mlflow subfolder
                        def img = docker.build("${DOCKER_USER_NAME}/microservices-mlflow", "microservices/mlflow")
                        img.push('latest')
                    }
                }
            }
        }

        stage('Deploy ELK Stack') {
            when { expression { env.ELK_CHANGED == 'true' } }
            steps {
                build job: 'elk-deployment', wait: false
            }
        }

        stage('Run Ansible Deployment') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(credentialsId: 'AWS_CREDENTIALS', passwordVariable: 'AWS_SECRET_ACCESS_KEY', usernameVariable: 'AWS_ACCESS_KEY_ID'),
                        string(credentialsId: 'AnsibleVaultCred', variable: 'VAULT_PASS')
                    ]) {
                        ansiblePlaybook(
                            playbook: 'ansible/deploy.yml',
                            inventory: 'ansible/inventory',
                            vaultCredentialsId: 'AnsibleVaultCred',
                            extraVars: [
                                aws_access_key: "${AWS_ACCESS_KEY_ID}",
                                aws_secret_key: "${AWS_SECRET_ACCESS_KEY}"
                            ]
                        )
                    }
                }
            }
        }
    }

    post {
        success {
            mail to: "${EMAIL_TO},203ajmk@gmail.com,aieshah.nasir@iiitb.ac.in",
                 subject: "SUCCESS: Skill-Ex Build '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                 body: "Great news! The Skill-Ex microservices were successfully built and deployed.\n\nBuild URL: ${env.BUILD_URL}"
        }
        failure {
            mail to: "${EMAIL_TO},203ajmk@gmail.com,aieshah.nasir@iiitb.ac.in",
                 subject: "FAILURE: Skill-Ex Build '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                 body: "Attention: The Skill-Ex build failed. Please check the logs immediately.\n\nBuild URL: ${env.BUILD_URL}"
        }
    }
}
