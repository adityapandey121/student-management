# `.gitignore` entries explained

| Entry | Why it is ignored |
|-------|-------------------|
| `__pycache__/`, `*.py[cod]` | Python creates compiled bytecode (`.pyc`, `.pyo`, `.pyd`) when it imports modules. These are machine-generated, change on every run and differ between Python versions, so they only add noise to diffs. |
| `.venv/` | The local virtual environment holds installed packages (hundreds of MB, OS-specific). Anyone can recreate it from `requirements*.txt`. |
| `.env` | Local environment variables, often containing passwords or tokens. Committing it would leak secrets into Git history forever. |
| `.vscode/`, `.idea/` | Personal editor/IDE settings. They differ per developer and are not part of the project. |
| `.pytest_cache/` | pytest's cache of last-failed tests. Local only. |
| `reports/` | Test reports produced by local runs and by the CI pipeline. CI archives them as build artifacts instead of committing them. |
| `*.log` | Runtime logs are generated output. |
| `!samples/*.log` | Exception to the rule above: the sample log files in `samples/` are **test inputs** for the log analyser, so they must be committed. The `!` re-includes them. |

`.gitattributes` complements this: it forces LF line endings for shell
scripts, Python files, the `Dockerfile` and the `Jenkinsfile`, so a Windows
checkout (`core.autocrlf=true`) does not turn them into CRLF and break `bash`
inside Linux containers and Jenkins agents.
