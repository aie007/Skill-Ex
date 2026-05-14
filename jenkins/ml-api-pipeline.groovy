pipeline {
    agent any

    environment {
        IMAGE_NAME = 'anujajose/microservices-ml-api'
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/anuja-jmk/Skill-Ex.git'
            }
        }

        // stage('Test') {
        //     steps {
        //         dir('microservices/ml-api') {
        //             sh '''
        //                 // shell script to test ml api
        //             '''
        //         }
        //     }
        // }

        stage('Build Docker Image') {
            steps {
                dir('microservices/ml-api') {
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
            echo 'ml api pipeline completed successfully!'
        }
        always {
            cleanWs()
        }
    }
}