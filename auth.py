import bcrypt
from datetime import datetime
from fastapi import HTTPException, Request

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_session(request: Request):
    session = request.session.get("user")
    if session is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session_expiration = datetime.fromisoformat(session["expires_at"])
    if datetime.now() > session_expiration:
        del request.session["user"]
        raise HTTPException(status_code=401, detail="Session expired")
    return session
