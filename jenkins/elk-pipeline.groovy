pipeline {
    agent any

    environment {
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
    }

    stages {
        stage('Deploy ELK Stack') {
            steps {

                echo "Applying Logstash..."
                sh 'kubectl apply -f elk/logstash/logstash-configmap.yaml -n skill-ex-demo'
                sh 'kubectl apply -f elk/logstash/logstash-deployment.yaml -n skill-ex-demo'
                
                echo "Applying Elasticsearch..."
                sh 'kubectl apply -f elk/elasticsearch/elasticsearch-deployment.yaml -n skill-ex-demo'

                echo "Applying Kibana..."
                sh 'kubectl apply -f elk/kibana/kibana-deployment.yaml -n skill-ex-demo'

                echo "Setting up Filebeat RBAC..."
                sh 'kubectl apply -f elk/filebeat/filebeat-rbac.yaml -n skill-ex-demo'

                echo "Applying Filebeat Config and DaemonSet..."
                sh 'kubectl apply -f elk/filebeat/filebeat-configmap.yaml -n skill-ex-demo'
                sh 'kubectl apply -f elk/filebeat/filebeat-k8s.yaml -n skill-ex-demo'
            }
        }
    }
}