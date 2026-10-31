"""The app SpeedHack generated for a run, served sandboxed so it can never reach SpeedHack itself."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.services import auth, generator, store

router = APIRouter(prefix="/api/prototypes", tags=["prototypes"])

HEADERS = {
    "Content-Security-Policy": generator.CSP,  # sandboxed, offline, only SpeedHack may frame it
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


OWN_RUN = [Depends(auth.own_run("No existe ese proyecto"))]


@router.get("/{run_id}", response_class=HTMLResponse, dependencies=OWN_RUN)
@router.get("/{run_id}/", response_class=HTMLResponse, dependencies=OWN_RUN)
def get_prototype(run_id: str):
    if not generator.RUN_ID.match(run_id) or store.get_run(run_id) is None:
        raise HTTPException(404, "No existe ese proyecto")
    path = generator.prototype_path(run_id)
    if not path.exists():
        raise HTTPException(404, "Este proyecto todavía no tiene un prototipo generado")
    return HTMLResponse(path.read_text(encoding="utf-8"), headers=HEADERS)
