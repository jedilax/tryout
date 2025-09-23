pipeline {
  agent any
  stages {
    stage('VM2') {
      steps {
        sshagent(credentials: ['jedissh']) {
          withCredentials([usernamePassword(credentialsId: 'jedilax', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
            sh """
set -euxo pipefail
ssh -o StrictHostKeyChecking=no surapatpp@172.20.10.5 /bin/bash -lc '
  set -euxo pipefail
  cd ~/tryout
  git pull --ff-only origin master || git pull --ff-only origin main
  docker ps -q --filter "name=simple-api" | xargs -r docker stop
  docker ps -aq --filter "name=simple-api" | xargs -r docker rm
  docker build -t ghcr.io/jedilax/tryout:latest .
  echo "${GH_PAT}" | docker login ghcr.io -u "${GH_USER}" --password-stdin
  docker push ghcr.io/jedilax/tryout:latest
  docker logout ghcr.io || true
'
"""
          }
        }
      }
    }

    stage('VM3') {
      steps {
        sshagent(credentials: ['jedissh']) {
          withCredentials([usernamePassword(credentialsId: 'jedilax', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
            sh """
set -euxo pipefail
ssh -o StrictHostKeyChecking=no surapatpp@172.20.10.7 /bin/bash -lc '
  set -euxo pipefail
  echo "${GH_PAT}" | docker login ghcr.io -u "${GH_USER}" --password-stdin || true
  docker ps -q --filter "name=simple-api" | xargs -r docker stop
  docker ps -aq --filter "name=simple-api" | xargs -r docker rm
  docker pull ghcr.io/jedilax/tryout:latest
  docker run -d --name simple-api -p 5000:5000 ghcr.io/jedilax/tryout:latest
'
"""
          }
        }
      }
    }
  }
}
