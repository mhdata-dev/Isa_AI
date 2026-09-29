"""Create only this stack's secrets; never rotate existing credentials implicitly."""
import os
from pathlib import Path
import secrets

ROOT=Path(__file__).resolve().parents[1]
os.umask(0o077)
directory=ROOT/'secrets'
directory.mkdir(mode=0o700,exist_ok=True)
directory.chmod(0o700)
for name in ('postgres_admin','n8n_database','n8n_encryption','garmin_writer','garmin_reader','collector_api'):
    path=directory/name
    if path.exists():
        continue
    with path.open('x') as file:
        file.write(secrets.token_urlsafe(48))
    # Compose mounts each individual file only into its intended service.
    # The host parent remains root-only; container non-root users need read access.
    path.chmod(0o444)
(ROOT/'runtime').mkdir(mode=0o700,exist_ok=True)
print('Secrets provisioned locally. No credential values were printed.')
