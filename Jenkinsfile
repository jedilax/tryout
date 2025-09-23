pipeline {
  agent any
  options { timestamps() }

  environment {
    REGISTRY     = 'ghcr.io'
    REGISTRY_NS  = 'jedilax'          // ghcr.io/<owner>
    IMAGE_NAME   = 'simple-api'

    // pre-init so post{} won't break if a stage fails early
    IMAGE_TAG    = ''
    FULL_IMAGE   = ''
    LATEST_IMAGE = ''
  }

  parameters {
    string(name: 'SIMPLE_API_REPO', defaultValue: 'https://github.com/jedilax/tryout.git')
    string(name: 'ROBOT_REPO',      defaultValue: 'https://github.com/jedilax/ConsoleApp2.git')
    string(name: 'MAIN_BRANCH',     defaultValue: 'master')
    booleanParam(name: 'CLEAN_STATE', defaultValue: true, description: 'Remove old container before deploy')
  }

  stages {
    stage('Checkout & Set Tags') {
      steps {
        git branch: params.MAIN_BRANCH, url: params.SIMPLE_API_REPO
        script {
          env.COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
          env.IMAGE_TAG    = "${env.BUILD_NUMBER}-${env.COMMIT_SHORT}"
          env.FULL_IMAGE   = "${env.REGISTRY_NS}/${env.IMAGE_NAME}:${env.IMAGE_TAG}"
          env.LATEST_IMAGE = "${env.REGISTRY_NS}/${env.IMAGE_NAME}:latest"
          echo "IMAGE_TAG: ${env.IMAGE_TAG}"
          echo "FULL_IMAGE: ${env.FULL_IMAGE}"
        }
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -U pip
          [ -f requirements.txt ] && pip install -r requirements.txt || true
          pip install pytest || true
          pytest -q --junitxml=test-results/unit.xml || true
        '''
      }
      post { always { junit allowEmptyResults: true, testResults: 'test-results/unit.xml' } }
    }

    stage('Build Image & Run (Test)') {
      steps {
        sh """
          docker build -t ${env.FULL_IMAGE} -t ${env.LATEST_IMAGE} .
          docker rm -f simple-api || true
          docker run -d --name simple-api -p 5000:5000 ${env.FULL_IMAGE}
          for i in {1..30}; do curl -fsS http://172.20.10.5:5000/health && break || sleep 2; done
        ""
      }
    }

    stage('Robot Tests') {
      steps {
        dir('robot') {
          git url: params.ROBOT_REPO, branch: params.MAIN_BRANCH
          sh '''
            python3 -m venv .venv
            . .venv/bin/activate
            pip install -U pip
            pip install robotframework robotframework-requests
            mkdir -p reports
            robot -d reports -v BASE_URL:http://172.20.10.5:5000 .
          '''
        }
      }
      post { always { archiveArtifacts artifacts: 'robot/reports/**', fingerprint: true } }
    }

    stage('Push Image to GHCR') {
      environment { GHCR = credentials('ghcr-jenkins') } // GitHub username + PAT
      steps {
        sh """
          echo "${GHCR_PSW}" | docker login -u "${GHCR_USR}" --password-stdin ${env.REGISTRY}
          docker push ${env.FULL_IMAGE}
          docker push ${env.LATEST_IMAGE}
        """
      }
    }

    stage('Deploy (same machine)') {
      steps {
        sh """
          ${params.CLEAN_STATE ? "docker rm -f simple-api-pre || true" : ":"}
          docker pull ${env.FULL_IMAGE}
          docker run -d --name simple-api-pre '-p' 8080:5000 --restart unless-stopped ${env.FULL_IMAGE}
        """
      }
    }

    stage('Health Check (8080)') {
      steps {
        sh """
          for i in {1..30}; do curl -fsS http://172.20.10.6:8080/health && break || sleep 2; done
          curl -fsS http://localhost:8080/health
        """
      }
    }
  }

  post {
    always {
      echo "Done. Image: ${env.FULL_IMAGE ?: '(not built)'}"
    }
  }
}
