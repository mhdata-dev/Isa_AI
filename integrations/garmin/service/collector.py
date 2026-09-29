import hmac
import time
import uvicorn
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.routing import Route
from common import read_secret, parse_day
from garmin_client import snapshot, session_available, SyncError

TOKEN=read_secret('COLLECTOR_TOKEN_FILE')
cooldown_until=0.0


def authorized(request):
    return hmac.compare_digest(request.headers.get('authorization',''), 'Bearer '+TOKEN)


async def health(request):
    return JSONResponse({'status':'ok'})


async def status(request):
    if not authorized(request):
        return JSONResponse({'error':'unauthorized'},status_code=401)
    return JSONResponse({'session_available':session_available(),'rate_limit_cooldown':time.monotonic()<cooldown_until})


async def daily(request):
    global cooldown_until
    if not authorized(request):
        return JSONResponse({'error':'unauthorized'},status_code=401)
    try:
        day=request.path_params['day']
        parse_day(day)
    except ValueError:
        return JSONResponse({'error':'invalid_date'},status_code=400)
    if time.monotonic()<cooldown_until:
        return JSONResponse({'error':'garmin_rate_limited'},status_code=429,headers={'Retry-After':'900'})
    try:
        data=await run_in_threadpool(snapshot,day)
        return JSONResponse(data,headers={'Cache-Control':'no-store'})
    except SyncError as error:
        if error.status==429:
            cooldown_until=time.monotonic()+900
        return JSONResponse({'error':error.code},status_code=error.status)
    except Exception:
        return JSONResponse({'error':'collector_unavailable'},status_code=502)


app=Starlette(routes=[Route('/healthz',health),Route('/status',status),Route('/snapshot/{day}',daily)])
if __name__=='__main__':
    uvicorn.run(app,host='0.0.0.0',port=8000,access_log=False,log_level='warning')
