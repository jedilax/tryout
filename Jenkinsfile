pipeline {
  agent none
  options { timestamps() }

  environment {
    REGISTRY     = 'ghcr.io'
    REGISTRY_NS  = 'jedilax'                 // <— OK for GHCR: ghcr.io/<owner>/<image>
    IMAGE_NAME   = 'simple-api'

    // init so post{} never crashes even if early stages fail
    IMAGE_TAG    = ''
    FULL_IMAGE   = ''
    LATEST_IMAGE = ''
  }

  parameters {
    string(name: 'SIMPLE_API_REPO', defaultValue: 'https://github.com/jedilax/tryout.git')
    string(name: 'ROBOT_REPO',      defaultValue: 'https://github.com/jedilax/ConsoleApp2.git')
    string(name: 'MAIN_BRANCH',     defaultValue: 'master')
    booleanParam(name: 'CLEAN_STATE', defaultValue: true, description: 'Clean old containers before deploy')
  }
  
  stage('VM2: Checkout simple-api & set tags') {
    agent { label 'vm2' }
    steps {
      git branch: params.MAIN_BRANCH, url: params.SIMPLE_API_REPO
      script {
        // assign straight to env.* instead of "def"
        env.COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
        env.IMAGE_TAG    = "${env.BUILD_NUMBER}-${env.COMMIT_SHORT}"
        env.FULL_IMAGE   = "${env.REGISTRY_NS}/${env.IMAGE_NAME}:${env.IMAGE_TAG}"
        env.LATEST_IMAGE = "${env.REGISTRY_NS}/${env.IMAGE_NAME}:latest"
  
        echo "IMAGE_TAG: ${env.IMAGE_TAG}"
        echo "FULL_IMAGE: ${env.FULL_IMAGE}"
      }
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
          pip install pytest || true
          pytest -q --junitxml=test-results/unit.xml || true
        '''
      }
      post { always { junit allowEmptyResults: true, testResults: 'test-results/unit.xml' } }
    }

    stage('VM2: Build Image & Run Container') {
      agent { label 'vm2' }
      steps {
        sh """
          docker build -t ${env.FULL_IMAGE} -t ${env.LATEST_IMAGE} .
          docker rm -f simple-api || true
          docker run -d --name simple-api -p 5000:5000 ${env.FULL_IMAGE}
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
      post { always { archiveArtifacts artifacts: 'robot/reports/**', fingerprint: true } }
    }

    stage('VM2: Push Image to GHCR') {
      agent { label 'vm2' }
      // Create Jenkins credential "ghcr-jenkins" (Username + PAT as password), or convert to Secret Text if you prefer
      environment { GHCR = credentials('ghcr-jenkins') }
      steps {
        sh """
          echo "${GHCR_PSW}" | docker login -u "${GHCR_USR}" --password-stdin ${env.REGISTRY}
          docker push ${env.FULL_IMAGE}
          docker push ${env.LATEST_IMAGE}
        """
      }
    }

    /* ================= VM3 (Pre-Prod) ================= */
    stage('VM3: Deploy Image') {
      agent { label 'vm3' }
      steps {
        sh """
          ${params.CLEAN_STATE ? "docker rm -f simple-api || true" : ":"}
          docker pull ${env.FULL_IMAGE}
          docker run -d --name simple-api -p 8080:5000 --restart unless-stopped ${env.FULL_IMAGE}
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
      echo "Pipeline finished. Image built: ${env.FULL_IMAGE ?: '(not built)'}"
    }
  }
