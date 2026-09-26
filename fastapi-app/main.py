from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.database import engine, Base
from models import user, product  # ensure tables are registered before create_all
from routers import auth, users, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
app.include_router(products.router, prefix="/products")
