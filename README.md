# Student Management System

A beginner-friendly Python project for practicing Git, automation scripts,
CI/CD with Jenkins and Docker. It contains:

- `main.py`: the original interactive command-line app
- `app.py`: the same features as a small web API (Flask), used for Docker
- `scripts/`: operational Bash and Python scripts

## Features
- Add students
- View all students
- Search by student ID
- Delete students
- Count students

## Requirements
- Python 3.10 or newer
- Git
- A GitHub account

## Run the project
```bash
python main.py                      # interactive CLI, no dependencies

pip install -r requirements.txt     # web API
python app.py                       # http://localhost:5000/health
```

## Build and run with Docker
```bash
docker build -t student-management:latest .
docker run -d --name sm -p 5000:5000 student-management:latest
curl http://localhost:5000/health
```

With Redis via Docker Compose:
```bash
cp .env.example .env                # set REDIS_PASSWORD; .env is never committed
docker compose up -d --build
curl http://localhost:5000/health   # {"status":"ok","storage":"redis"}
docker compose down
```

API endpoints, image design, test evidence and the port and environment
variable troubleshooting exercises are in [docs/docker.md](docs/docker.md).

## CI/CD with Jenkins
Every branch and pull request is built by Jenkins using the
[`Jenkinsfile`](Jenkinsfile): checkout, validate, unit tests (JUnit report),
Docker build, Compose + Redis smoke test, then reports and artifacts. A failing
test or validation fails the build.

Run the preconfigured local Jenkins:
```bash
cp jenkins/.env.example jenkins/.env      # set the admin and Redis CI passwords
docker compose -f jenkins/docker-compose.yml up -d --build
# open http://localhost:8095
```

Details, credentials handling and run evidence, including a diagnosed failed
build: [docs/jenkins.md](docs/jenkins.md).

## Operations scripts
Bash and Python scripts for routine checks live in `scripts/`:

```bash
bash scripts/disk_usage.sh -t 80 /                 # disk usage, warn above 80%
bash scripts/log_analyser.sh samples/*.log          # ERROR/WARN/INFO counts
python scripts/summarize.py samples/students.json   # JSON or text summary
```

See [docs/scripts.md](docs/scripts.md) for all options, error handling and
sample output.

## Running the tests
```bash
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest -v
```

## GitHub practice workflow
1. Create an empty GitHub repository named `student-management`.
2. Initialize and push this project to `main`.
3. Create a feature branch: `git switch -c feature/student-count`.
4. Make a change, then run `git diff` and `git status`.
5. Commit: `git add main.py && git commit -m "Add student count feature"`.
6. Push: `git push -u origin feature/student-count`.
7. Open a Pull Request on GitHub from `feature/student-count` into `main`.
8. Review and merge the PR, then update local `main`.

## Note
The CLI and the API without Redis store data in memory, so records reset when
the program exits. With Docker Compose the data is kept in a Redis volume.
