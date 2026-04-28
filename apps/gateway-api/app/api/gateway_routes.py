from fastapi import APIRouter, File as UploadFileType, HTTPException, UploadFile

from app.clients import audit_client, auth_client, file_client, policy_client


router = APIRouter(tags=["gateway"])


@router.post("/login")
async def login(
    email: str,
    password: str,
):
    return await auth_client.login(
        email=email,
        password=password,
    )


@router.post("/upload")
async def upload(
    token: str,
    file: UploadFile = UploadFileType(...),
):
    user = await auth_client.me(token)

    decision = await policy_client.evaluate(
        role=user["role"],
        resource="FILE",
        action="UPLOAD",
        clearance_level=1,
        risk_score=10,
    )

    if decision["decision"] != "ALLOW":
        raise HTTPException(
            status_code=403,
            detail=decision,
        )

    if "id" not in user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    content = await file.read()

    uploaded = await file_client.upload(
        owner_id=user["id"],
        filename=file.filename or "unknown",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )

    await audit_client.log(
        actor=user["id"],
        action="UPLOAD",
        resource="FILE",
        ip="127.0.0.1",
        result="SUCCESS",
    )

    return {
        "user": user,
        "file": uploaded,
        "message": "Upload successful",
    }