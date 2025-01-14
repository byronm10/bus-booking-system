import os
from fastapi import APIRouter, HTTPException
from backend.services.sdk import get_db, Base, engine
from backend.services import backend_services

router = APIRouter()

##############################################################################
#   Ambiente                                                    ##############
###############################################################################
stage = os.getenv("STAGE") if os.getenv("STAGE") else "dev"

if stage == "dev":
    print("Running in development mode -> ", stage)
#### End Ambiente ##############



# Re-insert admin user if needed
@router.on_event("startup")
async def startup_event():
    
    async with get_db() as db:  # Assuming get_db() is an async context manager
        startup_srv = backend_services()
        await startup_srv.create_admin_user(db)
    