pipeline {
  agent none
  options { timestamps(); ansiColor('xterm') }

  environment {
    REGISTRY     = 'docker.io'
    REGISTRY_NS  = 'your_dockerhub_username'     // change this
    IMAGE_NAME   = 'simple-api'
    COMMIT_SHORT = "${env.GIT_COMMIT?.take(7) ?: 'local'}"
    IMAGE_TAG    = "${env.BUILD_NUMBER}-${COMMIT_SHORT}"
    LATEST_IMAGE = "${REGISTRY_NS}/${IMAGE_NAME}:latest"
    FULL_IMAGE   = "${REGISTRY_NS}/${IMAGE_NAME}:${IMAGE_TAG}"
  }

  parameters {
    string(name: 'SIMPLE_API_REPO', defaultValue: 'https://github.com/your-org/simple-api.git')
    string(name: 'ROBOT_REPO',      defaultValue: 'https://github.com/your-org/simple-api-robot.git')
    string(name: 'MAIN_BRANCH',     defaultValue: 'main')
    booleanParam(name: 'CLEAN_STATE', defaultValue: true, description: 'Clean old containers before deploy')
  }

  stages {
    /* ================= VM2 (Test) ================= */
    stage('VM2: Checkout simple-api') {
      agent { label 'vm2' }
      steps {
        git branch: params.MAIN_BRANCH, url: params.SIMPLE_API_REPO
      }
    }

    stage('VM2: Unit Tests') {
      agent { label 'vm2' }
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -U pip
          [ -f requirements.txt ] && pip install -r requirements.txt || true
          pip install pytest
          pytest -q --junitxml=test-results/unit.xml
        '''
      }
      post {
        always { junit 'test-results/unit.xml' }
      }
    }

    stage('VM2: Build Image & Run Container') {
      agent { label 'vm2' }
      steps {
        sh """
          docker build -t ${FULL_IMAGE} -t ${LATEST_IMAGE} .
          docker rm -f simple-api || true
          docker run -d --name simple-api -p 5000:5000 ${FULL_IMAGE}
          for i in {1..30}; do curl -fsS http://localhost:5000/health && break || sleep 2; done
        """
      }
    }

    stage('VM2: Robot Tests') {
      agent { label 'vm2' }
      steps {
        dir('robot') {
          git url: params.ROBOT_REPO, branch: params.MAIN_BRANCH
          sh '''
            python3 -m venv .venv
            . .venv/bin/activate
            pip install -U pip
            pip install robotframework robotframework-requests
            mkdir -p reports
            robot -d reports -v BASE_URL:http://localhost:5000 .
          '''
        }
      }
      post {
        always { archiveArtifacts artifacts: 'robot/reports/**', fingerprint: true }
      }
    }

    stage('VM2: Push Image to Registry') {
      agent { label 'vm2' }
      environment { DOCKERHUB = credentials('dockerhub-username-password') }
      steps {
        sh """
          echo "${DOCKERHUB_PSW}" | docker login -u "${DOCKERHUB_USR}" --password-stdin ${REGISTRY}
          docker push ${FULL_IMAGE}
          docker push ${LATEST_IMAGE}
        """
      }
    }

    /* ================= VM3 (Pre-Prod) ================= */
    stage('VM3: Deploy Image') {
      agent { label 'vm3' }
      steps {
        sh """
          ${params.CLEAN_STATE ? "docker rm -f simple-api || true" : ":"}
          docker pull ${FULL_IMAGE}
          docker run -d --name simple-api -p 8080:5000 --restart unless-stopped ${FULL_IMAGE}
        """
      }
    }

    stage('VM3: Health Check') {
      agent { label 'vm3' }
      steps {
        sh """
          for i in {1..30}; do curl -fsS http://localhost:8080/health && break || sleep 2; done
          curl -fsS http://localhost:8080/health
        """
      }
    }
  }

  post {
    always {
      echo "Pipeline finished. Image built: ${FULL_IMAGE}"
    }
  }
}
