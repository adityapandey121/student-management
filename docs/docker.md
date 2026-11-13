# Docker and Docker Compose

The web API (`app.py`) is packaged as a Docker image and can run on its own
(in-memory storage) or with Redis through Docker Compose.

## Image design

| Choice | Why |
|--------|-----|
| `python:3.12-slim` base | Official image, small (≈190 MB final), no compilers needed since all deps ship wheels. |
| `requirements.txt` copied and installed before the code | The dependency layer is cached; editing `app.py` does not reinstall packages. |
| Non-root `appuser` (uid 10001) | A compromised app cannot modify the image or act as root in the container. |
| Only `app.py`, `storage.py`, `main.py` copied | `.dockerignore` keeps `.git`, `.env`, `.venv`, tests, docs and caches out of the build context and the image. |
| `EXPOSE 5000`, `PORT` env var | Documents the port. `PORT` can change it at runtime. |
| `HEALTHCHECK` on `/health` | `docker ps` shows `healthy`/`unhealthy`. |
| gunicorn, 1 worker + 4 threads | Production WSGI server. A single worker so in-memory storage is shared between requests. |
| No secrets in the image | The Redis password is passed at runtime from `.env`. |

## Run the image alone (in-memory storage)

```bash
docker build -t student-management:latest .
docker run -d --name sm -p 5000:5000 student-management:latest

curl http://localhost:5000/health
curl -X POST http://localhost:5000/students \
     -H "Content-Type: application/json" \
     -d '{"id": "S1", "name": "Alice", "course": "Math"}'
curl http://localhost:5000/students
curl http://localhost:5000/students/count
curl -X DELETE http://localhost:5000/students/S1

docker rm -f sm
```

PowerShell alternative for the POST:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/students `
  -ContentType application/json -Body '{"id":"S1","name":"Alice","course":"Math"}'
```

The original interactive CLI is still in the image:
`docker run --rm -it student-management:latest python main.py`

## Run with Docker Compose (app + Redis)

```bash
cp .env.example .env          # then edit REDIS_PASSWORD
docker compose up -d --build
docker compose ps             # both services should be "healthy"
curl http://localhost:5000/health    # {"status":"ok","storage":"redis"}
docker compose logs -f app
docker compose down           # add -v to also delete the Redis volume
```

Without `.env`, Compose refuses to start:

```text
error while interpolating services.app.environment.REDIS_URL: required variable REDIS_PASSWORD is missing a value: Set REDIS_PASSWORD in .env (see .env.example)
```

Data is stored in the `redis-data` volume, so students survive
`docker compose restart app` and `docker compose down` (but not `down -v`).

## Test evidence

Recorded on Docker Desktop 29.8 (Linux engine), Windows 11.

```text
$ docker run -d --name sm-test -p 5000:5000 student-management:dev
$ curl -s localhost:5000/health
{"status":"ok","storage":"memory"}
$ curl -s -X POST localhost:5000/students -H 'Content-Type: application/json' -d '{"id":"S1","name":"Alice","course":"Math"}'
{"course":"Math","id":"S1","name":"Alice"}
$ curl -s localhost:5000/students/count
{"count":1}
$ docker exec sm-test id
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
$ docker ps --filter name=sm-test --format '{{.Status}} {{.Ports}}'
Up 18 seconds (healthy) 0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
$ docker run --rm --entrypoint ls student-management:dev -A /app
app.py
main.py
requirements.txt
storage.py
```

Compose, including persistence across an app restart:

```text
$ docker compose up -d --build
 Container student-management-demo-redis-1 Healthy
 Container student-management-demo-app-1 Started
$ curl -s localhost:5000/health
{"status":"ok","storage":"redis"}
$ curl -s -X POST localhost:5000/students -H 'Content-Type: application/json' -d '{"id":"S1","name":"Alice","course":"Math"}'
{"course":"Math","id":"S1","name":"Alice"}
$ docker compose restart app
$ curl -s localhost:5000/students
[{"course":"Math","id":"S1","name":"Alice"}]
```

Checking that no secret is baked into the image:

```text
$ docker image inspect student-management:latest --format '{{json .Config.Env}}'
["PATH=...","LANG=C.UTF-8","GPG_KEY=...","PYTHON_VERSION=3.12.16",...,"PYTHONDONTWRITEBYTECODE=1","PYTHONUNBUFFERED=1","PIP_NO_CACHE_DIR=1","PIP_DISABLE_PIP_VERSION_CHECK=1","PORT=5000"]
$ docker history --no-trunc student-management:latest | grep -ci "redis_password\|secret"
0
```

(`GPG_KEY` is the public key the official Python image uses to verify its
download. It is not a secret.)

## Troubleshooting exercises

### 1. Wrong port mapping

**Symptom.** The container is "Up" but the API does not answer.

```text
$ docker run -d --name sm-wrongport -p 5050:8000 student-management:latest
150dcb421436
$ curl -sS --max-time 5 http://localhost:5050/health
curl: (52) Empty reply from server
# exit code: 52
$ docker ps --filter name=sm-wrongport --format "{{.Names}}  {{.Status}}  {{.Ports}}"
sm-wrongport  Up 4 seconds (health: starting)  0.0.0.0:5050->8000/tcp, [::]:5050->8000/tcp
$ docker logs sm-wrongport
[2026-11-12 08:03:01 +0000] [1] [INFO] Starting gunicorn 23.0.0
[2026-11-12 08:03:01 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
[2026-11-12 08:03:01 +0000] [1] [INFO] Using worker: gthread
[2026-11-12 08:03:01 +0000] [7] [INFO] Booting worker with pid: 7
```

**Diagnosis.**
- `curl: (52) Empty reply from server` means Docker accepted the connection on
  host port 5050, but nothing in the container listens on the target port.
- `docker ps` shows the mapping `5050->8000/tcp`.
- `docker logs` shows gunicorn `Listening at: http://0.0.0.0:5000`.
- The mapping sends traffic to container port **8000**, but the app listens on
  **5000**.

**Fix.** Map to the port the app actually listens on. In `-p HOST:CONTAINER`,
CONTAINER must equal `PORT` (default 5000):

```text
$ docker rm -f sm-wrongport && docker run -d --name sm -p 5050:5000 student-management:latest
f30063192d74
$ curl -sS http://localhost:5050/health
{"status":"ok","storage":"memory"}
```

**Side note found during the exercise.** The first attempt used host port
8080 and failed immediately with
`ports are not available: ... bind: Only one usage of each socket address ... is normally permitted`.
Another program on the laptop already used 8080. That is the *host* side of
the mapping. Choose a free host port, or find the owner with
`netstat -ano | findstr :8080` (Windows) or `ss -ltnp | grep 8080` (Linux).

### 2. Wrong environment variable

**Symptom.** `/health` returns HTTP 503 with `REDIS_URL` pointing at
`redis-db` instead of the Compose service name `redis`.

The first time this was tried, the logs only showed the 503 access log line,
which did not explain the cause. The app was therefore changed (commit "Log why
Redis is unreachable") to log the real error and the target host, with the
password masked. With that change:

```text
$ docker run -d --name sm-badenv --network student-management-demo_default -p 5051:5000 -e REDIS_URL='redis://:x@redis-db:6379/0' student-management:latest
d25171a3ac05
$ curl -s localhost:5051/health
{"detail":"ConnectionError: Error -5 connecting to redis-db:6379. No address associated with hostname.","status":"error","storage":"redis","target":"redis-db:6379/0"}
  (HTTP 503)
$ docker logs sm-badenv
[2026-11-12 08:03:53 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
[2026-11-12 08:03:53,581] INFO in app: Using redis storage (redis-db:6379/0)
[2026-11-12 08:04:01,152] ERROR in storage: Redis at redis-db:6379/0 is unreachable: ConnectionError: Error -5 connecting to redis-db:6379. No address associated with hostname.
172.21.0.1 - - [12/Nov/2026:08:04:01 +0000] "GET /health HTTP/1.1" 503 167 "-" "curl/8.21.0"
```

**Diagnosis.** `No address associated with hostname` for `redis-db:6379`
means the hostname does not resolve. On a Compose network, containers
reach each other by **service name**, and the Redis service is called
`redis` (`docker compose ps` / `docker-compose.yml`).

**Fix.** Use `redis://:<password>@redis:6379/0`. That is what
`docker-compose.yml` builds from `.env`.

```text
$ docker run -d --name sm-goodenv --network student-management-demo_default -p 5051:5000 -e REDIS_URL="redis://:$PW@redis:6379/0" student-management:latest
$ curl -s localhost:5051/health
{"status":"ok","storage":"redis"}  (HTTP 200)
$ docker logs sm-goodenv | grep Using
INFO in app: Using redis storage (redis:6379/0)
```

Other variable mistakes and how they show up:

| Mistake | What you see |
|---------|--------------|
| `REDIS_PASSWORD` missing from `.env` | `docker compose up` refuses to start with "required variable REDIS_PASSWORD is missing a value". |
| Wrong password in `REDIS_URL` | `/health` returns 503. The log shows an authentication error from Redis. |
| `PORT=8000` but mapping still `5000:5000` | Same as exercise 1. Logs show `Listening at: http://0.0.0.0:8000`. |
