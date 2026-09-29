"""Interactive only: credentials go directly from the user's terminal to Garmin."""
from getpass import getpass
import logging
import os
import sys
from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectTooManyRequestsError, GarminConnectConnectionError
from garmin_client import SESSION_DIR, session_lock, SyncError


def failure_message(error):
    # Inspect types/status codes only. Upstream messages can contain account data.
    chain=[]
    current=error
    while current is not None and id(current) not in {id(e) for e in chain}:
        chain.append(current)
        current=current.__cause__ or current.__context__
    statuses={getattr(getattr(e,'response',None),'status_code',None) for e in chain}
    if 429 in statuses or any(isinstance(e,GarminConnectTooManyRequestsError) for e in chain):
        return '[garmin_rate_limited] A Garmin limitou as requisições deste acesso (HTTP 429). Aguarde antes de tentar novamente; não repita o login agora.'
    if any(isinstance(e,PermissionError) for e in chain):
        return '[session_permission] Sem permissão para gravar a sessão Garmin.'
    if isinstance(error,SyncError):
        return '[session_busy] Já existe uma autorização ou sincronização em andamento.'
    if 403 in statuses:
        return '[garmin_access_denied] A Garmin recusou o acesso (HTTP 403). Pode haver uma restrição ao acesso pela VPS.'
    if any(isinstance(e,GarminConnectAuthenticationError) for e in chain):
        return '[garmin_auth_failed] A Garmin não concluiu a autenticação. Isso pode envolver a conta, a verificação adicional ou uma restrição do serviço.'
    if any(isinstance(e,GarminConnectConnectionError) for e in chain):
        return '[garmin_connection] Falha de comunicação com a Garmin. A senha não foi confirmada como incorreta.'
    return '[garmin_unexpected] Falha interna na autorização. Os detalhes foram ocultados para proteger sua conta.'


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Run interactively: docker compose exec garmin-collector python login.py')
    logging.disable(logging.CRITICAL)
    os.umask(0o077)
    print('Autorização Garmin. A senha e o código não serão exibidos nem gravados.')
    try:
        with session_lock():
            # Hide email as well, to keep terminal recordings free of account identifiers.
            email=getpass('Email Garmin (oculto): ').strip()
            password=getpass('Senha Garmin: ')
            api=Garmin(email=email,password=password,prompt_mfa=lambda:getpass('Código de verificação Garmin: ').strip())
            del email,password
            api.login(str(SESSION_DIR))
            print('Sessão Garmin autorizada. A sincronização pode começar.')
    except KeyboardInterrupt:
        raise SystemExit('Login cancelado.') from None
    except Exception as error:
        raise SystemExit(failure_message(error)) from None


if __name__=='__main__':
    main()
