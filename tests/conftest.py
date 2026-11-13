import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SAMPLES = ROOT / "samples"

sys.path.insert(0, str(SCRIPTS))

BASH = shutil.which("bash")


@pytest.fixture
def run_bash():
    """Run a script from scripts/ with bash and return the CompletedProcess."""
    if BASH is None:
        pytest.skip("bash is not installed")

    def _run(script, *args, env=None):
        return subprocess.run(
            [BASH, str(SCRIPTS / script), *map(str, args)],
            capture_output=True, text=True, cwd=ROOT, env=env,
        )

    return _run
