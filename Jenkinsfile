// CI pipeline for student-management.
// Runs for every branch and pull request discovered by the Multibranch job
// (see jenkins/ and docs/jenkins.md). Any failing command fails the build.
pipeline {
    agent any

    options {
        skipDefaultCheckout()          // we check out explicitly in the first stage
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE_NAME = 'student-management'
        // Docker tags and compose project names allow only a limited charset.
        SAFE_BRANCH = "${env.BRANCH_NAME.toLowerCase().replaceAll('[^a-z0-9_-]', '-')}"
        IMAGE_TAG = "${SAFE_BRANCH}-${env.BUILD_NUMBER}"
        COMPOSE_PROJECT_NAME = "smci-${SAFE_BRANCH}-${env.BUILD_NUMBER}"
        COMPOSE = 'docker compose -f docker-compose.yml -f docker-compose.ci.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty="Building %h (%an): %s"'
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    set -eu
                    echo "== Python syntax"
                    python3 -m py_compile main.py app.py storage.py scripts/summarize.py ci/smoke_test.py
                    echo "OK"
                    echo "== Bash syntax"
                    for f in scripts/*.sh; do bash -n "$f"; echo "OK  $f"; done
                    echo "== Compose files"
                    REDIS_PASSWORD=validate-only IMAGE_TAG=validate $COMPOSE config --quiet
                    echo "OK"
                '''
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .venv
                    .venv/bin/pip install --quiet --disable-pip-version-check -r requirements-dev.txt
                    mkdir -p reports
                    .venv/bin/python -m pytest -v --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: true
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --pull --tag "$IMAGE_NAME:$IMAGE_TAG" .'
            }
        }

        stage('Smoke test (Compose + Redis)') {
            steps {
                // The Redis password comes from the Jenkins credential store
                // and is masked (****) in the console log.
                withCredentials([string(credentialsId: 'redis-ci-password', variable: 'REDIS_PASSWORD')]) {
                    sh '''
                        set -eu
                        $COMPOSE up --detach --no-build --wait --wait-timeout 90
                        $COMPOSE ps
                        $COMPOSE exec -T app python - < ci/smoke_test.py
                    '''
                }
            }
            post {
                always {
                    withCredentials([string(credentialsId: 'redis-ci-password', variable: 'REDIS_PASSWORD')]) {
                        sh '''
                            mkdir -p reports
                            $COMPOSE logs --no-color --timestamps > reports/compose.log 2>&1 || true
                            $COMPOSE down --volumes --remove-orphans || true
                        '''
                    }
                }
            }
        }

        stage('Reports & artifacts') {
            steps {
                sh '''
                    set -eu
                    mkdir -p reports dist
                    bash scripts/log_analyser.sh reports/compose.log | tee reports/log-levels.txt
                    python3 scripts/summarize.py samples/students.json --format json > reports/students-summary.json
                    # disk_usage.sh exits 1 on a threshold warning: report it, don't fail the build
                    bash scripts/disk_usage.sh -t 90 / > reports/disk-usage.txt || [ $? -eq 1 ]
                    cat reports/disk-usage.txt
                    docker image inspect "$IMAGE_NAME:$IMAGE_TAG" \
                        --format 'tags={{.RepoTags}} id={{.Id}} size={{.Size}} created={{.Created}}' | tee reports/image.txt
                    git archive --format=tar.gz --output "dist/student-management-$IMAGE_TAG-src.tar.gz" HEAD
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true, fingerprint: true
            sh 'docker image rm "$IMAGE_NAME:$IMAGE_TAG" >/dev/null 2>&1 || true'
            cleanWs()
        }
        success {
            echo "Build OK: ${env.IMAGE_NAME}:${env.IMAGE_TAG} validated, tested and smoke-tested."
        }
        failure {
            echo 'Build FAILED. Open the first red stage in the stage view and read its log; failed tests are listed under "Tests".'
        }
    }
}
