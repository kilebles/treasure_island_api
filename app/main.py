import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.database.db import init_db
from app.routes import router


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(BASE_DIR, 'static')):
    os.mkdir(os.path.join(BASE_DIR, 'static'))

app = FastAPI(title="Treasure Island API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    '/uploads',
    StaticFiles(directory='app/static'),
    name='uploads'
)

init_db(app)
app.include_router(router)