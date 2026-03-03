from pathlib import Path

from pyramid.response import FileResponse, Response
from pyramid.view import view_config


@view_config(route_name='home')
def home_view(request):
    index_path = Path(__file__).resolve().parents[3] / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), request=request)

    return Response("Frontend index.html not found.", status=500)
