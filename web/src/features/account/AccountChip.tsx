import { Button } from "../../lib/ui";
import { resetText, runsLeftText, signIn, signOut, useAccount } from "./store";
import "./account.css";

// Top bar: "Entrar con Google" without a session; the email, the runs left today and "Salir" with one.
export function AccountChip() {
  const { status, user, signInError, needsSignIn } = useAccount();
  if (status === "loading") return <div className="account" aria-hidden="true" />;
  if (!user) {
    return (
      <div className="account">
        <Button onClick={signIn}>Entrar con Google</Button>
        {signInError && !needsSignIn && (
          <p className="account__error" role="alert">
            {signInError}
          </p>
        )}
      </div>
    );
  }
  const reset = user.runs_left_today <= 0 ? resetText(user.resets_at) : null;
  return (
    <div className="account">
      <div className="account__who">
        <span className="account__email" title={user.email}>
          {user.email}
        </span>
        <span className="account__left" role="status">
          {runsLeftText(user.runs_left_today)}
          {reset && ` · se renueva el ${reset}`}
        </span>
      </div>
      <Button onClick={signOut}>Salir</Button>
    </div>
  );
}

// A 401 from any call lands here instead of as an error message.
export function SignInPrompt() {
  const { needsSignIn, user, signInError } = useAccount();
  if (!needsSignIn || user) return null;
  return (
    <div className="account__prompt" role="alert">
      <p>Inicia sesión con Google para continuar. Así tus proyectos son solo tuyos.</p>
      {signInError && <p className="account__error">{signInError}</p>}
      <Button variant="primary" onClick={signIn}>
        Entrar con Google
      </Button>
    </div>
  );
}
