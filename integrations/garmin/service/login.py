"""Interactive only: credentials go directly from the user's terminal to Garmin."""
from getpass import getpass
import logging
import os
import sys
from garminconnect import Garmin
from garmin_client import SESSION_DIR, session_lock


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
    except Exception:
        raise SystemExit('Não foi possível autorizar. Confira suas credenciais e tente novamente mais tarde.') from None


if __name__=='__main__':
    main()
