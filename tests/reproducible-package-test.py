"""Compare committed bytes with a rebuild under a restrictive umask."""
from pathlib import Path
import os, subprocess, sys, tempfile
root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as tmp:
    old_umask = os.umask(0o077)
    try:
        subprocess.run([sys.executable, str(root/'build/package.py'),
                        '--no-publish', '--output-dir', tmp], check=True)
    finally:
        os.umask(old_umask)
    for name in ['UGREEN-DXP4800Pro-LEDs.plg', 'UGREEN-DXP4800Pro-LEDs.plg.sha256']:
        assert (root/name).read_bytes() == (Path(tmp)/name).read_bytes(), name
print('Committed package matches a rebuild with restrictive umask; build leaves committed artifacts unchanged.')
