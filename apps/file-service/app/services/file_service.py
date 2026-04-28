from sqlalchemy.orm import Session

from app.models.file import File


def create_file(
    db: Session,
    owner_id: str,
    filename: str,
    stored_name: str,
    mime_type: str,
    size: int,
    sha256: str,
    sensitivity: str = "INTERNAL",
):
    file = File(
        owner_id=owner_id,
        filename=filename,
        stored_name=stored_name,
        mime_type=mime_type,
        size=size,
        sha256=sha256,
        sensitivity=sensitivity,
        status="ACTIVE",
        risk_score=0,
    )

    db.add(file)
    db.commit()
    db.refresh(file)

    return file


def get_file(
    db: Session,
    file_id: str,
):
    return (
        db.query(File)
        .filter(File.id == file_id)
        .first()
    )


def list_files(db: Session):
    return db.query(File).all()


def delete_file(
    db: Session,
    file_id: str,
):
    file = get_file(db, file_id)

    if file is None:
        return None

    db.delete(file)
    db.commit()

    return file