import { Chip, MOMENTS, SectionHeader } from "../../lib/ui";
import "./landing.css";

export const path = "/";
export const label = "Inicio";
export const order = 0;

// The three moments people go through (web/DESIGN.md) and what each one gives back.
const STEPS: Record<(typeof MOMENTS)[number]["label"], string> = {
  Idea: "Me la cuentas y respondes 3 preguntas cortas.",
  Plan: "Investigo con fuentes reales; al aprobar, Miro y Linear se llenan solos.",
  Producto: "Prototipo revisado y un pitch que puedes defender.",
};

const PLANS = [
  { name: "Gratis", text: "Tu idea, las preguntas, la investigación con fuentes y tu plan." },
  { name: "Pro", text: "Todo lo anterior con tablero en Miro, tareas en Linear, prototipo y pitch con preguntas por voz." },
  { name: "Equipos", text: "Memoria compartida entre personas y panel de costos por etapa." },
];

export default function Landing() {
  return (
    <div className="landing">
      <section className="landing__hero">
        <div className="landing__copy">
          <h1>De idea a pitch defendible en una hora</h1>
          <p>
            Cuéntame tu idea: investigo, planeo y te dejo prototipo y pitch. Tú decides en tres momentos.
          </p>
          <div className="landing__cta">
            <a className="sh-btn sh-btn--primary" href="#/intake">Contar mi idea</a>
            <a className="sh-btn sh-btn--secondary" href="#/project">Ver un ejemplo</a>
          </div>
        </div>
        <figure className="landing__shot">
          <img
            src={`${import.meta.env.BASE_URL}landing/conversation.png`}
            width={812}
            height={372}
            alt="Tarjeta de la conversación de SpeedHack: el plan de un SaaS de control de gastos con sus fuentes y los botones Sí, sigamos y Cambiar algo."
          />
          <figcaption>Captura real del ejemplo grabado.</figcaption>
        </figure>
      </section>

      <section className="landing__section">
        <SectionHeader title="Cómo funciona" meta="3 momentos" />
        <ol className="landing__steps">
          {MOMENTS.map((m, i) => (
            <li key={m.label}>
              <span className="landing__n" aria-hidden="true">{i + 1}</span>
              <div>
                <h3>{m.label}</h3>
                <p>{STEPS[m.label]}</p>
              </div>
            </li>
          ))}
        </ol>
        <p className="landing__note">
          Nada avanza sin ti: apruebas tu plan, las tareas y el prototipo, y en cada uno puedes pedir cambios.
        </p>
      </section>

      <section className="landing__section">
        <SectionHeader title="Planes" meta="Hipótesis de precios, por validar" />
        <div className="landing__plans">
          {PLANS.map((p) => (
            <article key={p.name}>
              <h3>{p.name}</h3>
              <p>{p.text}</p>
              <Chip>Precio por definir</Chip>
            </article>
          ))}
        </div>
        <p className="landing__note">Aún no hay cobro: la demo no usa pagos reales.</p>
      </section>

      <section className="landing__section landing__trust" aria-labelledby="privacidad">
        <h2 id="privacidad">Privacidad y voz</h2>
        <p>
          La voz del pitch es una IA y lo dice al empezar. Los mensajes del Agente Cazador solo se envían tras
          aprobación humana y con opción de baja. No usamos datos personales de reseñadores y los prospectos se
          borran a los 30 días (regla mostrada, no ejecutada en la demo).
        </p>
        <p>
          Marco legal de referencia: la nueva LFPDPPP, publicada el 20 de marzo de 2025 (
          <a href="https://www.garrigues.com/es_ES/noticia/mexico-nueva-ley-federal-proteccion-datos-personales-posesion-particulares-introduce">Garrigues</a>
          ,{" "}
          <a href="https://iapp.org/news/a/entendiendo-la-ley-federal-de-protecci-n-de-datos-personales-en-posesi-n-de-los-particulares-en-mexico">IAPP</a>
          ).
        </p>
      </section>

      <footer className="landing__ask">
        <h2>Cuéntame tu idea</h2>
        <a className="sh-btn sh-btn--primary" href="#/intake">Empezar</a>
        <small>Hacktoberfest Hack Day CDMX (MLH), 27 y 28 de octubre de 2026. Los negocios y prospectos son ficticios.</small>
      </footer>
    </div>
  );
}
