import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";

// Design tokens owned by HACK-003; eager so the build passes before the design lock.
import.meta.glob("./styles/*.css", { eager: true });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
