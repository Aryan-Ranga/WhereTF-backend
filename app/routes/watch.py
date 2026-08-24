import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import SessionLocal
from app.models import WatchedFolder

router = APIRouter(tags=["Watch"])


class WatchFolderRequest(BaseModel):
    folder_path: str


def get_validated_folder_path(folder_path: str) -> str:
    """
    Ensure a requested folder is visible to the backend container and lies
    within the configured Docker-mounted watch root.
    """
    watch_root = Path(os.getenv("WATCH_ROOT", "/watched_f")).resolve()
    resolved_folder = Path(folder_path).resolve()

    try:
        resolved_folder.relative_to(watch_root)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Folder must be inside the configured watch root: {watch_root}",
        )

    if not resolved_folder.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Folder does not exist inside the container: {resolved_folder}",
        )

    return str(resolved_folder)


@router.post("/watch/folder")
def add_watch_folder(req: WatchFolderRequest):
    folder_path = get_validated_folder_path(req.folder_path)
    db = SessionLocal()

    try:
        existing = db.query(WatchedFolder).filter_by(
            folder_path=folder_path
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Folder is already being watched.",
            )

        watched_folder = WatchedFolder(
            folder_path=folder_path
        )

        db.add(watched_folder)
        db.commit()
        db.refresh(watched_folder)

        return {
            "success": True,
            "id": watched_folder.id,
            "folder_path": watched_folder.folder_path,
        }

    finally:
        db.close()


@router.get("/watch/folders")
def get_watched_folders():
    db = SessionLocal()

    try:
        folders = db.query(WatchedFolder).all()

        return [
            {
                "id": folder.id,
                "folder_path": folder.folder_path,
                "created_at": folder.created_at,
            }
            for folder in folders
        ]

    finally:
        db.close()


@router.delete("/watch/folder")
def remove_watch_folder(req: WatchFolderRequest):
    folder_path = get_validated_folder_path(req.folder_path)
    db = SessionLocal()

    try:
        folder = db.query(WatchedFolder).filter_by(
            folder_path=folder_path
        ).first()

        if not folder:
            raise HTTPException(
                status_code=404,
                detail="Folder not found.",
            )

        db.delete(folder)
        db.commit()

        return {
            "success": True
        }

    finally:
        db.close()