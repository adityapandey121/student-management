# CI/CD with Jenkins

The pipeline is defined in [`Jenkinsfile`](../Jenkinsfile). A local Jenkins
controller, fully configured as code, lives in [`jenkins/`](../jenkins).

## Pipeline stages

| Stage | What it does | Fails the build when |
|-------|--------------|----------------------|
| Checkout | `checkout scm`, prints commit and author | repo cannot be fetched |
| Validate | `py_compile` on all Python files, `bash -n` on all scripts, `docker compose config` on both Compose files | any syntax / config error |
| Unit tests | Creates a venv, installs `requirements-dev.txt`, runs `pytest` → `reports/junit.xml` (published to Jenkins' *Tests* tab) | any test fails |
| Build image | `docker build --pull -t student-management:<branch>-<build>` | Dockerfile error |
| Smoke test (Compose + Redis) | Starts app + Redis with `docker-compose.yml` + `docker-compose.ci.yml` (`--wait` for healthchecks), runs [`ci/smoke_test.py`](../ci/smoke_test.py) inside the app container, then always saves logs and tears down | containers don't become healthy, or any API check fails |
| Reports & artifacts | Log-level counts of the container logs, JSON summary, disk usage, image info, source tarball | report step errors |

`post { always }` archives `reports/**` and `dist/**`, removes the build's
image and cleans the workspace. Each build uses its own Compose project name
and publishes no host ports, so parallel builds cannot collide.

Archived artifacts of a green build:

```text
dist/student-management-feature-jenkins-ci-2-src.tar.gz
reports/compose.log
reports/disk-usage.txt
reports/image.txt
reports/junit.xml
reports/log-levels.txt
reports/students-summary.json
```

## Triggers: push and pull request

The job is a **Multibranch Pipeline** (`student-management`). It discovers:

- every **branch** that contains a `Jenkinsfile` (push → new commit → build), and
- every **pull request** through GitHub's `refs/pull/<N>/head` refs. Each PR
  appears as job `PR-<N>`.

Normally GitHub would notify Jenkins through a webhook
(`http://<jenkins>/github-webhook/` or `.../git/notifyCommit`). This lab Jenkins
runs on `localhost`, which GitHub cannot reach, so the job **scans the repo
every 2 minutes** (`periodicFolderTrigger`). A push or a new PR is built
within 2 minutes. *Scan Multibranch Pipeline Now* starts a build immediately.

## Credentials

No secret is in the repo, the Jenkinsfile or the image:

- The Redis password used by the smoke test is a **Secret text credential**
  `redis-ci-password` in the Jenkins credential store. The pipeline reads it
  with `withCredentials([string(credentialsId: 'redis-ci-password', ...)])`,
  and Jenkins masks it as `****` in the console log.
- JCasC creates that credential and the admin user from environment variables
  in `jenkins/.env`. The file is git-ignored; [`jenkins/.env.example`](../jenkins/.env.example) shows its format.
- The GitHub repo is public, so checkout needs no credential. For a private repo,
  add a *Username with password* (GitHub PAT) credential and reference it
  with `credentialsId(...)` in the branch source.

Check that the secret never reached the log:

```text
$ grep -c "$REDIS_CI_PASSWORD" build2.log
0
[...] Masking supported pattern matches of $REDIS_PASSWORD
```

## Run Jenkins locally

Prerequisites: Docker Desktop (or Docker Engine) running.

```bash
cp jenkins/.env.example jenkins/.env      # choose an admin password and a Redis CI password
docker compose -f jenkins/docker-compose.yml up -d --build
docker compose -f jenkins/docker-compose.yml logs -f jenkins   # wait for "Jenkins is fully up and running"
```

Open <http://localhost:8095> and log in with the values from `jenkins/.env`.
The `student-management` job already exists. Click *Scan Multibranch
Pipeline Now* or wait 2 minutes.

How it is wired:
- `jenkins/Dockerfile`: Jenkins LTS 2.580.2 (JDK 21) + `python3`, `python3-venv`, the Docker CLI and the Compose plugin. Plugins come from `plugins.txt`, the setup wizard is disabled.
- `jenkins/casc.yaml`: admin user, credential, and the Multibranch job (Job DSL).
- `jenkins/docker-compose.yml`: publishes port 8095 (8080 was already taken on the dev laptop) and mounts `/var/run/docker.sock` so the pipeline can build and run containers. `group_add: "0"` gives the `jenkins` user access to the socket without running Jenkins as root.

> Mounting the Docker socket gives Jenkins full control of the host's Docker.
> That is acceptable for a local lab. In a shared setup, use a dedicated build
> agent or a rootless builder instead.

Stop it with `docker compose -f jenkins/docker-compose.yml down` (add `-v`
to delete jobs and history).

## Run evidence

Branch `feature/jenkins-ci`:

| Build | Commit | Result | Notes |
|------:|--------|--------|-------|
| #1 | `c844de9` Add local Jenkins controller set up as code | ❌ FAILURE | Unexpected failure in *Unit tests*. See "Failure 1" below. |
| #2 | `7952a24` Fix CI: stop pytest collecting ci/smoke_test.py | ✅ SUCCESS | 31/31 tests, smoke test passed, 7 artifacts archived |
| #3 | `98ad638` Rename count response field to total | ❌ FAILURE | Deliberate safe failure. See "Failure 2" below. |
| #4 | `9cd6321` Revert "Rename count response field to total" | ✅ SUCCESS | 31/31 tests, all stages green |

### Failure 1 (unplanned): pytest collected the smoke test

Console log of build #1, stage *Unit tests*:

```text
collecting ... collected 31 items / 1 error
______________________ ERROR collecting ci/smoke_test.py _______________________
ci/smoke_test.py:35: in <module>
    status, body = call("GET", "/health")
...
E   ValueError: unknown url type: '-v/health'
ERROR ci/smoke_test.py - ValueError: unknown url type: '-v/health'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
Stage "Build image" skipped due to earlier failure(s)
```

**Diagnosis.** The error is in *collecting* `ci/smoke_test.py`, a file that
is not a unit test. pytest's default file pattern is `test_*.py` **or
`*_test.py`**, so `smoke_test.py` matched. Importing it ran the HTTP calls at
module level, and `sys.argv[1]` was pytest's own `-v` flag, which explains the
URL `-v/health`. It passed on the laptop only because `ci/` did not exist when
the tests were last run there.

**Fix** (commit `7952a24`): add `pytest.ini` with `testpaths = tests`, and
move the smoke checks into `main()` behind `if __name__ == "__main__"`.
Build #2 passed.

### Failure 2 (deliberate): breaking the API contract

To practise the fail → diagnose → fix loop, commit `98ad638` renamed the JSON
field returned by `GET /students/count` from `count` to `total`.

Console log of build #3:

```text
Building 98ad638 (Aditya): Rename count response field to total (intentional CI failure exercise)
tests/test_app.py::test_add_list_get_count_delete FAILED                 [  6%]
>       assert client.get("/students/count").get_json() == {"count": 1}
E       AssertionError: assert {'total': 1} == {'count': 1}
FAILED tests/test_app.py::test_add_list_get_count_delete - AssertionError: assert {'total': 1} == {'count': 1}
========================= 1 failed, 30 passed in 0.29s =========================
Stage "Build image" skipped due to earlier failure(s)
Stage "Smoke test (Compose + Redis)" skipped due to earlier failure(s)
Stage "Reports & artifacts" skipped due to earlier failure(s)
Build FAILED. Open the first red stage in the stage view and read its log; failed tests are listed under "Tests".
Finished: FAILURE
```

Jenkins' *Tests* tab showed `failCount: 1, passCount: 30`.

**Diagnosis.** The `Building <sha>` line identifies the commit. The failed
assertion shows the exact difference (`total` vs `count`). The later stages
were skipped, so no broken image was built or tested.

**Fix** (commit `9cd6321`): `git revert` the change, since the field is part of the
public API. Build #4 passed with 31/31 tests.
