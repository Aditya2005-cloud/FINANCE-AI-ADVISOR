from pathlib import Path

from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from .models import Base, DBSession


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def main(global_config, **settings):
    config = Configurator(settings=settings)

    engine = engine_from_config(settings, 'sqlalchemy.')

    DBSession.configure(bind=engine)
    session_factory = sessionmaker(bind=engine)

    config.registry.db_session_factory = session_factory

    config.include("pyramid_jinja2")

    config.add_static_view(name='frontend', path=str(FRONTEND_DIR), cache_max_age=0)

    config.add_route('home', '/')
    config.add_route('predict', '/predict')
    config.add_route('api_predict', '/api/predict')
    config.add_route('predictions', '/predictions')
    config.add_route('api_predictions', '/api/predictions')
    config.add_route('ai_analyze', '/ai/analyze')
    config.add_route('api_ai_analyze', '/api/ai/analyze')
    config.add_route('ai_chat', '/ai/chat')
    config.add_route('api_ai_chat', '/api/ai/chat')

    config.scan("finance_ai.views")

    return config.make_wsgi_app()
