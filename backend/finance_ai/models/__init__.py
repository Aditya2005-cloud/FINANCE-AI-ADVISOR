from .meta import Base
from .prediction_log import PredictionLog
from sqlalchemy.orm import sessionmaker

DBSession = sessionmaker()

def includeme(config):
    from sqlalchemy import engine_from_config

    settings = config.get_settings()

    engine = engine_from_config(settings, prefix="sqlalchemy.")
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine