pipeline {
    agent any
    triggers {
        pollSCM('* * * * *') // Poll every 1 minutes; adjust as needed
    }
    stages {
        stage('Checkout') {
            steps {
                // Clone or pull the latest code
                checkout scm
            }
        }
        stage('VM2') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'jedilax', passwordVariable: 'GIT_PSSWD', usernameVariable: 'GIT_USER')]) {
                    sshagent (credentials: ['jedissh']) {
                        sh '''
                        ssh -o StrictHostKeyChecking=no surapatpp@172.20.10.6 "
                        # ไปที่ home directory
                        cd ~
                        # เข้าไปที่ project
                        cd tryout
                        docker stop simple-api
                        docker rm simple-api
                        git pull origin master
                        
                        # สร้าง/อัปเดต image และ start service
                        docker build -t simple-api:latest .
                        docker run -d --name simple-api -p 5000:5000 simple-api:latest
                        cd ConsoleApp2/
                        git pull origin master
                        robot tests/api_tests.robot
                        echo $GIT_PSSWD | docker login ghcr.io -u $GIT_USER --password-stdin
                        docker tag simple-api:latest ghcr.io/jedilax/simple-api:latest
                        docker push ghcr.io/jedilax/simple-api:latest
                        "
                        '''
                    }
                }
            }
        }
        stage('VM3') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'jedilax', passwordVariable: 'GIT_PSSWD', usernameVariable: 'GIT_USER')]) {
                    sshagent (credentials: ['jedissh']) {
                        sh '''
                        ssh -o StrictHostKeyChecking=no surapatpp@172.20.10.7 "
                        echo $GIT_PSSWD | docker login ghcr.io -u $GIT_USER --password-stdin
                        docker stop simple-api || true
                        docker rmi ghcr.io/jedilax/simple-api:latest || true
                        docker pull ghcr.io/jedilax/tryout:latest
                        docker run -d -p 5000:5000 --name simple-api --rm ghcr.io/jedilax/tryout:latest
                        "
                        '''
                    }
                }
            }
        }
    }
}
