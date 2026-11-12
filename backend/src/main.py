import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from redis import Redis
from src.config.database import Base,engine
from src.config.settings import SEED_DEMO,REDIS_URL
from src.models import *
from src.middlewares.request_id import RequestIDMiddleware
from src.middlewares.errors import ErrorMiddleware
from src.routes import auth,catalog,runs,notes,audit

def _ensure_run_snapshot_columns():
 # 对已存在的库幂等补列；须先于任何ORM访问与seed执行，新建库由create_all建出同结构
 from sqlalchemy import inspect
 inspector=inspect(engine)
 if 'correspondence_runs' not in inspector.get_table_names():return
 existing={c['name'] for c in inspector.get_columns('correspondence_runs')}
 is_sqlite=engine.dialect.name=='sqlite'
 with engine.begin() as conn:
  if 'input_snapshot' not in existing:
   default="'{}'" if is_sqlite else "'{}'::json"
   conn.execute(text(f"ALTER TABLE correspondence_runs ADD COLUMN input_snapshot JSON DEFAULT {default}"))
  if 'input_fingerprint' not in existing:
   conn.execute(text("ALTER TABLE correspondence_runs ADD COLUMN input_fingerprint VARCHAR(64) DEFAULT ''"))
  indexes={i['name'] for i in inspector.get_indexes('correspondence_runs')}
  if 'ix_correspondence_runs_input_fingerprint' not in indexes:
   conn.execute(text("CREATE INDEX ix_correspondence_runs_input_fingerprint ON correspondence_runs (input_fingerprint)"))

@asynccontextmanager
async def lifespan(app):
 _ensure_run_snapshot_columns()
 Base.metadata.create_all(engine)
 _ensure_run_snapshot_columns()
 if SEED_DEMO:
  try:
   from scripts.seed_demo import seed
   seed()
  except Exception:logging.exception('Seed failure; startup continues')
 yield
app=FastAPI(title='禾陌展陈偏好对应图',lifespan=lifespan)
app.add_middleware(ErrorMiddleware);app.add_middleware(RequestIDMiddleware)
for route in (auth,catalog,runs,notes,audit):app.include_router(route.router)
@app.get('/health')
def health():
 with engine.connect() as c:c.execute(text('select 1'))
 Redis.from_url(REDIS_URL).ping();return {'status':'ok'}
