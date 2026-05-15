pipeline {
    agent any

    environment {
        IMAGE_NAME = 'anujajose/microservices-dashboard'
        KUBECONFIG = '/var/lib/jenkins/.kube/config'   
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/aie007/Skill-Ex.git'
            }
        }

        // stage('Test') {
        //     steps {
        //         dir('microservices/dashboard') {
        //             // shell script to test dashboard
        //         }
        //     }
        // }

        stage('Build Docker Image') {
            steps {
                dir('microservices/dashboard') {
                    sh 'docker build -t $IMAGE_NAME:latest .'
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh 'docker push $IMAGE_NAME:latest'
                }
            }
        }
    }

    post {
        failure {
            emailext (
                subject: "Pipeline Failed: ${currentBuild.fullDisplayName}",
                body: "Something went wrong :( ${env.BUILD_URL}",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
        success {
            echo 'dashboard pipeline completed successfully!'
        }
        always {
            cleanWs()
        }
    }
}