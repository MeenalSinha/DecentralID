from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.exceptions import DecentralIDException
from backend.app.middleware.correlation import CorrelationIdMiddleware
from backend.app.middleware.exceptions import decentralid_exception_handler, generic_exception_handler
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.blockchain import router as blockchain_router
from backend.app.api.routes.authentication import router as authentication_router
from backend.app.api.routes.organizations import router as organizations_router
from backend.app.api.routes.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    await init_db()
    yield
    # Shutdown actions

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DecentralID Verifiable Credential Infrastructure API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Exception Handlers
app.add_exception_handler(DecentralIDException, decentralid_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(blockchain_router, prefix=settings.API_V1_STR)
app.include_router(authentication_router, prefix=settings.API_V1_STR)
app.include_router(organizations_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
