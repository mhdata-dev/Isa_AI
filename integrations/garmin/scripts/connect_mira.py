"""Register only Garmin in the signed-in Isa user's MCP list; no saved login."""
from getpass import getpass
from http.cookiejar import CookieJar
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import build_opener,HTTPCookieProcessor,Request

BASE='http://127.0.0.1:8080'
MCP_URL='http://isa-garmin-mcp:8000/mcp'


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Execute em um terminal SSH interativo.')
    opener=build_opener(HTTPCookieProcessor(CookieJar()))
    token=None
    def api(method,path,payload=None):
        headers={'Content-Type':'application/json'}
        if token: headers['Authorization']='Bearer '+token
        request=Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers,method=method)
        with opener.open(request,timeout=60) as response:
            body=response.read()
        return json.loads(body) if body else None
    print('Conectar Garmin à Isa. Digite as credenciais da ISA/MIRA, não as da Garmin.')
    try:
        login={'username':getpass('Usuário da Isa (oculto): ').strip(),'password':getpass('Senha da Isa: ')}
        session=api('POST','/api/auth/login',login)
        del login
        token=session['access_token']
        del session
        existing=next((row for row in api('GET','/api/mcp/servers') if row.get('name')=='garmin'),None)
        if existing:
            config=existing.get('config',existing)
            if isinstance(existing.get('config_json'),str): config=json.loads(existing['config_json'])
            if config.get('url')!=MCP_URL:
                raise SystemExit('Já existe um servidor garmin diferente. Nenhuma alteração foi feita nele.')
            # Refresh tool discovery after adding check-in tools, without restarting Isa.
            api('PUT','/api/mcp/servers/'+existing['id'],{'enabled':True})
            print('O servidor Garmin já está cadastrado.')
        else:
            api('POST','/api/mcp/servers',{'name':'garmin','transport':'http','url':MCP_URL,'enabled':True,'sampling_enabled':False})
            print('Servidor Garmin cadastrado na sua conta da Isa.')
        statuses=api('GET','/api/mcp/status')
        garmin=next((row for row in statuses if row.get('name')=='garmin'),None)
        if garmin and garmin.get('state')=='connected' and garmin.get('tool_count',0)>=3:
            print('Isa conectada ao Garmin MCP; ferramentas disponíveis: '+str(garmin['tool_count']))
        else:
            raise SystemExit('Cadastro salvo, mas a conexão ainda não foi confirmada. Confira o estado MCP na Isa.')
    except HTTPError as error:
        raise SystemExit(f'A Isa recusou a operação (HTTP {error.code}). Nenhuma credencial foi exibida.') from None
    except (URLError,TimeoutError):
        raise SystemExit('Não foi possível alcançar a Isa. Tente novamente quando ela estiver disponível.') from None
    except KeyboardInterrupt:
        raise SystemExit('Configuração cancelada.') from None
    finally:
        if token:
            try: api('POST','/api/auth/logout',{})
            except Exception: pass


if __name__=='__main__': main()
