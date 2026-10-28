import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" };

// Primary = the one action that moves the run forward (approve, start). Everything else is secondary.
export function Button({ variant = "secondary", className = "", ...rest }: Props) {
  return <button type="button" className={`sh-btn sh-btn--${variant} ${className}`} {...rest} />;
}
