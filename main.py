from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from routers import user_router, session_router, subaccounts_router, transactions_router, payments_router, deposits_router

security = HTTPBearer()

app = FastAPI(
    title="Original Backend API",
    description="""
    API documentation for the Original backend services.
    
    ## Authentication
    To use protected endpoints, click the 'Authorize' button and enter your token in the format:
    ```
    Bearer your_session_token
    ```
    Get your session token by using the /v1/session/login endpoint.
    """,
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
    openapi_tags=[
        {
            "name": "users",
            "description": "Operations related to user management"
        },
        {
            "name": "sessions",
            "description": "User session management operations"
        },
        {
            "name": "subaccounts",
            "description": "Operations for managing sub-accounts"
        },
        {
            "name": "transactions",
            "description": "Transaction-related operations"
        },
        {
            "name": "payments",
            "description": "Payment processing operations"
        },
        {
            "name": "deposits",
            "description": "Deposit management operations"
        },
        {
            "name": "health",
            "description": "API health check endpoints"
        }
    ]
)

origins = [
    # "http://localhost:5173/", # vue dev
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    return credentials.credentials

# Include routers with their tags
app.include_router(
    user_router.router,
    prefix="/v1",
    tags=["users"],
    dependencies=[Depends(get_current_token)]
)
app.include_router(
    session_router.router,
    prefix="/v1",
    tags=["sessions"]
)
app.include_router(
    subaccounts_router.router,
    prefix="/v1",
    tags=["subaccounts"],
    dependencies=[Depends(get_current_token)]
)
app.include_router(
    transactions_router.router,
    prefix="/v1",
    tags=["transactions"],
    dependencies=[Depends(get_current_token)]
)
app.include_router(
    payments_router.router,
    prefix="/v1",
    tags=["payments"],
    dependencies=[Depends(get_current_token)]
)
app.include_router(
    deposits_router.router,
    prefix="/v1",
    tags=["deposits"],
    dependencies=[Depends(get_current_token)]
)

#app.mount("/", StaticFiles(directory = "../front/Original/dist"), name = "frontend")

@app.get("/v1/health", tags=["health"])
def get_health():
    """
    Check the health status of the API.
    
    Returns:
        dict: A dictionary containing the API status
    """
    return {"status": "ok"}