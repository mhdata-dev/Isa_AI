"""Complete the two user logins interactively; keep passwords out of chat/logs."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def run_step(command):
    result=subprocess.run(command,cwd=ROOT,check=False)
    if result.returncode:
        raise SystemExit('Etapa interrompida. As próximas etapas não foram executadas; consulte a mensagem acima.')

if not sys.stdin.isatty(): raise SystemExit('Use um terminal SSH interativo.')
print('1/3 — Autorizar a conta Garmin.')
run_step(['docker','compose','exec','garmin-collector','python','login.py'])
print('2/3 — Executar a primeira sincronização pelo n8n (pode levar alguns minutos).')
run_step([sys.executable,str(ROOT/'scripts/run_sync.py')])
print('3/3 — Cadastrar o MCP na sua conta da Isa.')
run_step([sys.executable,str(ROOT/'scripts/connect_mira.py')])
print('Etapas concluídas. Na Isa, consulte o estado de sincronização Garmin.')
