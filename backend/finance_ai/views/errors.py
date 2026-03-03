from pyramid.httpexceptions import HTTPException
from pyramid.response import Response
from pyramid.view import exception_view_config


@exception_view_config(context=Exception)
def api_exception_view(exc, request):
    path = request.path or ""
    accept = request.headers.get("Accept", "")
    wants_json = path.startswith("/api/") or "application/json" in accept
    if not wants_json:
        return exc

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        message = exc.detail or exc.explanation or str(exc)
    else:
        status_code = 500
        message = str(exc) or "Internal server error"

    payload = f'{{"status":"error","message":"{message.replace(chr(34), chr(39))}"}}'
    return Response(
        body=payload,
        status=status_code,
        content_type="application/json",
        charset="utf-8",
    )
