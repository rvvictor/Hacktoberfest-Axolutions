import type { ReactNode } from "react";

// One turn of the conversation: SpeedHack on the left with its avatar, the person on the right.
export function Message({ from = "speedhack", children }: { from?: "speedhack" | "you"; children: ReactNode }) {
  return (
    <div className={from === "you" ? "sh-msg sh-msg--you" : "sh-msg"}>
      {from === "speedhack" && (
        <span className="sh-msg__avatar" aria-hidden="true">
          S
        </span>
      )}
      <div className="sh-msg__bubble">{children}</div>
    </div>
  );
}
