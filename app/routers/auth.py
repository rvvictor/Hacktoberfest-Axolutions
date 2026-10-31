"""Sign in with Google and the current session (spec 001)."""
from urllib.parse import urlsplit

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from app.config import settings
from app.services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])
LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def _redirect_uri(request: Request) -> str:
    # Behind Render's proxy the request scheme is http; PUBLIC_URL names the address Google redirects to.
    if settings.PUBLIC_URL:
        return settings.PUBLIC_URL.rstrip("/") + "/api/auth/google/callback"
    return str(request.url_for("google_callback"))


def _secure(request: Request) -> bool:
    # Safari drops Secure cookies sent over http://localhost, which loses the state; only local plain http goes without.
    url = urlsplit(settings.PUBLIC_URL) if settings.PUBLIC_URL else request.url
    return not (url.scheme == "http" and url.hostname in LOOPBACK)


def _cookie(request: Request, response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(name, value, max_age=max_age, httponly=True, secure=_secure(request), samesite="lax", path="/")


@router.get("/google/login")
def google_login(request: Request) -> RedirectResponse:
    if not auth.configured():
        raise HTTPException(503, "El inicio de sesión con Google no está configurado todavía.")
    state, verifier, challenge = auth.new_flow()
    response = RedirectResponse(auth.authorize_url(_redirect_uri(request), state, challenge), status_code=302)
    _cookie(request, response, auth.FLOW_COOKIE, f"{state}.{verifier}", auth.FLOW_SECONDS)
    return response


@router.get("/google/callback", name="google_callback")
def google_callback(
    request: Request, code: str | None = None, state: str | None = None, error: str | None = None,
    sh_oauth: str | None = Cookie(default=None),
) -> RedirectResponse:
    expected, _, verifier = (sh_oauth or "").partition(".")
    try:
        if error or not code:
            raise auth.AuthError("google answered with an error")
        if not auth.same_state(expected, state or "") or not verifier:
            raise auth.AuthError("state mismatch")
        claims = auth.exchange(code, verifier, _redirect_uri(request))
    except auth.AuthError as exc:
        auth.log.warning("sign-in refused: %s", exc.reason)
        raise HTTPException(400, str(exc)) from None
    response = RedirectResponse("/#/", status_code=303)
    response.delete_cookie(auth.FLOW_COOKIE, path="/")
    _cookie(request, response, auth.SESSION_COOKIE, auth.start_session(claims), auth.SESSION_SECONDS)
    return response


@router.get("/me")
def get_me(sh_session: str | None = Cookie(default=None)) -> dict:
    user = auth.user_for(sh_session)
    if user is None:
        raise HTTPException(401, "Inicia sesión para continuar.")
    return auth.me(user)


@router.post("/logout", status_code=204)
def logout(sh_session: str | None = Cookie(default=None)) -> Response:
    auth.end_session(sh_session)
    response = Response(status_code=204)
    response.delete_cookie(auth.SESSION_COOKIE, path="/")
    return response
