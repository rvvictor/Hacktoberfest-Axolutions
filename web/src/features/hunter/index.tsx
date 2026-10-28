import { useCallback, useEffect, useState } from "react";

import { api } from "../../lib/api";
import { Button, Chip, DemoBadge, Item, Panel, Title } from "../../lib/ui";

type Stage = "draft" | "approved" | "sent" | "replied" | "skipped";

interface Outreach {
  id: string;
  prospect_id: string;
  channel: string;
  body: string;
  stage: Stage;
  approved_by: string | null;
  transport: string | null;
  call_allowed: boolean;
  demo_data: boolean;
}

interface ProspectRow {
  id: string;
  business: string;
  city: string;
  public_pain: string;
  public_source_url: string;
  channel: string;
  opt_out: boolean;
  retention_days: number;
  demo_data: boolean;
  outreach: Outreach | null;
}

interface Rules {
  rules: string[];
  retention_days: number;
}

export const path = "/hunter";
export const label = "Hunter";
export const order = 40;

const STAGES: Stage[] = ["draft", "approved", "sent", "replied"];
const STAGE_LABEL: Record<Stage, string> = {
  draft: "Borrador",
  approved: "Aprobado",
  sent: "Enviado (simulado)",
  replied: "Respondió",
  skipped: "Omitido: pidió baja",
};

function Progress({ stage }: { stage: Stage }) {
  if (stage === "skipped") return <Chip tone="error">{STAGE_LABEL.skipped}</Chip>;
  const at = STAGES.indexOf(stage);
  return (
    <ol className="flex flex-wrap gap-2" aria-label="Estado del mensaje">
      {STAGES.map((s, i) => (
        <li key={s} aria-current={i === at ? "step" : undefined}>
          <Chip tone={i < at ? "ok" : i === at ? "rosa" : "neutral"}>{STAGE_LABEL[s]}</Chip>
        </li>
      ))}
    </ol>
  );
}

function ProspectCard({ prospect, onChange }: { prospect: ProspectRow; onChange: () => void }) {
  const outreach = prospect.outreach;
  const [body, setBody] = useState(outreach?.body ?? "");
  const [operator, setOperator] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setBody(outreach?.body ?? ""), [outreach?.body]);

  const run = async (action: () => Promise<unknown>) => {
    setError(null);
    try {
      await action();
      onChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo falló");
    }
  };
  const post = (url: string, data?: unknown) =>
    api(url, { method: "POST", body: data === undefined ? undefined : JSON.stringify(data) });

  const editable = outreach?.stage === "draft";
  return (
    <Item tone={prospect.opt_out ? "ink" : "rosa"} code={prospect.city} meta={prospect.public_pain}>
      <div className="flex flex-col gap-3">
        <span>
          {prospect.business}{" "}
          <a href={prospect.public_source_url} className="text-sm underline">
            fuente pública
          </a>
        </span>
        {outreach && <Progress stage={outreach.stage} />}
        {!outreach && !prospect.opt_out && (
          <div>
            <Button onClick={() => run(() => post(`/hunter/prospects/${prospect.id}/draft`))}>Redactar borrador</Button>
          </div>
        )}
        {!outreach && prospect.opt_out && <Chip tone="error">Pidió baja: no se le escribe</Chip>}
        {outreach && outreach.stage !== "skipped" && (
          <>
            <textarea
              aria-label={`Mensaje para ${prospect.business}`}
              className="w-full rounded-[10px] border-2 border-[var(--sh-line)] p-3 text-sm"
              rows={5}
              value={body}
              readOnly={!editable}
              onChange={(e) => setBody(e.target.value)}
            />
            {editable && (
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={() => run(() => api(`/hunter/outreach/${outreach.id}`, { method: "PUT", body: JSON.stringify({ body }) }))}>
                  Guardar cambios
                </Button>
                <input
                  aria-label="Tu nombre"
                  placeholder="Tu nombre"
                  className="rounded-full border-2 border-[var(--sh-line)] px-4 py-2 text-sm"
                  value={operator}
                  onChange={(e) => setOperator(e.target.value)}
                />
                <Button
                  variant="primary"
                  disabled={!operator.trim()}
                  onClick={() =>
                    run(async () => {
                      await api(`/hunter/outreach/${outreach.id}`, { method: "PUT", body: JSON.stringify({ body }) });
                      await post(`/hunter/outreach/${outreach.id}/approve`, { approved_by: operator.trim() });
                    })
                  }
                >
                  Aprobar mensaje
                </Button>
              </div>
            )}
            {outreach.stage === "approved" && (
              <div>
                <Button variant="primary" onClick={() => run(() => post(`/hunter/outreach/${outreach.id}/send`))}>
                  Enviar (simulado)
                </Button>{" "}
                <small>Aprobó {outreach.approved_by}</small>
              </div>
            )}
            {outreach.stage === "sent" && (
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => run(() => post(`/hunter/outreach/${outreach.id}/reply`, { asks_for_call: false }))}>
                  Registrar respuesta
                </Button>
                <Button onClick={() => run(() => post(`/hunter/outreach/${outreach.id}/reply`, { asks_for_call: true }))}>
                  Respondió y pide llamada
                </Button>
              </div>
            )}
            {outreach.call_allowed && <Chip tone="ok">El negocio pidió una llamada</Chip>}
          </>
        )}
        {error && <p role="alert" className="text-sm text-[var(--sh-error)]">{error}</p>}
      </div>
    </Item>
  );
}

export default function Hunter() {
  const [prospects, setProspects] = useState<ProspectRow[] | null>(null);
  const [rules, setRules] = useState<Rules | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api<ProspectRow[]>("/hunter/prospects").then(setProspects).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    load();
    api<Rules>("/hunter/rules").then(setRules).catch((e: Error) => setError(e.message));
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-baseline justify-between gap-4">
        <Title>Hunter: prospectos con consentimiento</Title>
        <DemoBadge />
      </div>
      <div className="grid gap-6 [grid-template-columns:1.3fr_1fr] max-[820px]:[grid-template-columns:1fr]">
        <Panel title="Prospectos" meta={prospects ? `${prospects.length} negocios ficticios` : undefined}>
          {error && <p role="alert">No se pudo cargar: {error}</p>}
          {!prospects && !error && <p>Cargando…</p>}
          {prospects?.map((p) => (
            <ProspectCard key={p.id} prospect={p} onChange={load} />
          ))}
        </Panel>
        <Panel title="Reglas" meta={rules ? `${rules.retention_days} días de retención` : undefined}>
          <ul className="flex flex-col gap-3 text-sm">
            {(rules?.rules ?? []).map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
