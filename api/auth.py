from fastapi import APIRouter, Depends, HTTPException, Response, Request
from services.auth_service import AuthService
from deps.db import get_db
from config.config import load_config

router = APIRouter(prefix="/auth", tags=["auth"])
config = load_config()


@router.post("/login")
async def login(
    payload: dict,
    response: Response,
    conn=Depends(get_db),
):
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    service = AuthService(conn)
    user = await service.authenticate(username, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    response.set_cookie(
        key=config.auth.cookie_name,
        value=str(user["id"]),
        httponly=True,
        samesite="lax",
    )

    return {"success": True, "username": user["username"]}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(config.auth.cookie_name)
    return {"success": True}


@router.get("/me")
async def me(request: Request, conn=Depends(get_db)):
    user_id = request.cookies.get(config.auth.cookie_name)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    row = await conn.fetchrow(
        "SELECT id, username FROM users WHERE id=$1",
        int(user_id),
    )
    if not row:
        raise HTTPException(status_code=401, detail="Invalid session")

    return {"id": row["id"], "username": row["username"]}
