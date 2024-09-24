from fastapi import FastAPI
from app.routes import user
from fastapi.middleware.cors import CORSMiddleware


def create_application():
    application = FastAPI()
    application.include_router(user.user_router)
    application.include_router(user.guest_router)
    application.include_router(user.auth_router)
    return application


app = create_application()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hi, server working. Awesome - Your setup is done."}
