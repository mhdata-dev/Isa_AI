"""Complete the two user logins interactively; keep passwords out of chat/logs."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
if not sys.stdin.isatty(): raise SystemExit('Use um terminal SSH interativo.')
print('1/3 — Autorizar a conta Garmin.')
subprocess.run(['docker','compose','exec','garmin-collector','python','login.py'],cwd=ROOT,check=True)
print('2/3 — Executar a primeira sincronização pelo n8n (pode levar alguns minutos).')
subprocess.run([sys.executable,str(ROOT/'scripts/run_sync.py')],cwd=ROOT,check=True)
print('3/3 — Cadastrar o MCP na sua conta da Isa.')
subprocess.run([sys.executable,str(ROOT/'scripts/connect_mira.py')],cwd=ROOT,check=True)
print('Etapas concluídas. Na Isa, consulte o estado de sincronização Garmin.')
