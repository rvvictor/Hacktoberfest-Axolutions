// The intake only creates the project (POST /api/projects); the questions live in #/project.
export type { Mode, Run } from "../../lib/types";

export const STACKS = ["React", "Next.js", "Supabase", "FastAPI", "Postgres", "Tailwind"] as const;
