pipeline {
    agent {
        kubernetes {
            yaml """
                apiVersion: v1
                kind: Pod
                metadata:
                  labels:
                    jenkins: agent
                spec:
                  serviceAccountName: jenkins
                  containers:
                  - name: kaniko
                    image: gcr.io/kaniko-project/executor:debug
                    command:
                    - sleep
                    args:
                    - 9999999
                    volumeMounts:
                    - name: docker-config
                      mountPath: /kaniko/.docker
                      readOnly: true
                  - name: kubectl
                    image: alpine/k8s:1.28.13
                    command:
                    - sleep
                    args:
                    - 9999999
                  volumes:
                  - name: docker-config
                    secret:
                      secretName: docker-registry-config-kent
                      items:
                      - key: .dockerconfigjson
                        path: config.json
            """
        }
    }

    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_USERNAME = 'rcanonigo'
        APP_NAME = 'todo-webapp-observability'
        NAMESPACE = 'todo-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Build Image') {
            steps {
                container('kaniko') {
                    sh """
                        /kaniko/executor \
                          --dockerfile=Dockerfile \
                          --context=. \
                          --destination=${DOCKER_REGISTRY}/${DOCKER_USERNAME}/${APP_NAME}:${IMAGE_TAG} \
                          --destination=${DOCKER_REGISTRY}/${DOCKER_USERNAME}/${APP_NAME}:latest \
                          --cache=true \
                          --cache-repo=${DOCKER_REGISTRY}/${DOCKER_USERNAME}/cache
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    sh """
                        # Inject built image with tag into deployment before applying
                        sed "s|image: todoapp:latest|image: ${DOCKER_REGISTRY}/${DOCKER_USERNAME}/${APP_NAME}:${IMAGE_TAG}|g" k8s-deployment.yaml > k8s-deployment-temp.yaml

                        # Apply manifests
                        kubectl apply -f k8s-deployment-temp.yaml -n ${NAMESPACE}

                        # Wait for rollout to finish
                        kubectl rollout status deployment/todoapp -n ${NAMESPACE}
                    """
                }
            }
        }
    }
}
