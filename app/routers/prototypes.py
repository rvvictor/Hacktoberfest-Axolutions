"""The app SpeedHack generated for a run, served sandboxed so it can never reach SpeedHack itself."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services import generator, store

router = APIRouter(prefix="/api/prototypes", tags=["prototypes"])

# Inline code only, no network, and an opaque origin (CSP sandbox) even when opened in its own tab,
# so generated code cannot read SpeedHack's storage or call its API. Only SpeedHack may frame it.
CSP = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
    "font-src data:; form-action 'none'; frame-ancestors 'self'; sandbox allow-scripts allow-forms allow-modals"
)
HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


@router.get("/{run_id}", response_class=HTMLResponse)
@router.get("/{run_id}/", response_class=HTMLResponse)
def get_prototype(run_id: str):
    if not generator.RUN_ID.match(run_id) or store.get_run(run_id) is None:
        raise HTTPException(404, "No existe ese proyecto")
    path = generator.prototype_path(run_id)
    if not path.exists():
        raise HTTPException(404, "Este proyecto todavía no tiene un prototipo generado")
    return HTMLResponse(path.read_text(encoding="utf-8"), headers=HEADERS)
