import uvicorn
from app.config import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.APP_HOST, port=config.APP_PORT)