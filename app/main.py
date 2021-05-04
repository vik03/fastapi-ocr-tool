from fastapi import FastAPI
from . routers import extractor

app = FastAPI()

app.include_router(extractor.router)