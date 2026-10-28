import { Chip, MetroLine, SectionHeader } from "../../lib/ui";
import "./landing.css";

export const path = "/";
export const label = "Inicio";
export const order = 0;

const STEPS = [
  { n: "1", title: "Dicta o escribe tu idea", text: "Respondes unas preguntas técnicas o de negocio, sin jerga." },
  { n: "2", title: "Aprueba el spec", text: "SpeedHack investiga con fuentes citadas y tú apruebas antes de seguir." },
  { n: "3", title: "Mira cómo se llenan Miro y Linear", text: "Arquitectura y tickets salen del mismo spec, en la misma pantalla." },
];

const PLANS = [
  { name: "Gratis", text: "Idea, preguntas, investigación citada y spec." },
  { name: "Pro", text: "Todo lo anterior con tablero en Miro, backlog en Linear, prototipo y pitch con preguntas por voz." },
  { name: "Equipos", text: "Memoria compartida entre personas y panel de costos por etapa." },
];

export default function Landing() {
  return (
    <div className="landing">
      <section className="landing__hero">
        <div className="landing__copy">
          <h1>De idea a pitch defendible en una hora</h1>
          <p>
            SpeedHack convierte una idea dictada en investigación citada, arquitectura en Miro, backlog en
            Linear, un prototipo y un pitch con preguntas por voz, con un solo hilo de contexto.
          </p>
          <div className="landing__cta">
            <a className="sh-btn sh-btn--primary" href="#/intake">Probar la demo</a>
            <a className="sh-btn sh-btn--secondary" href="#/live-board">Ver el tablero en vivo</a>
          </div>
        </div>
        <figure className="landing__shot">
          <img
            src={`${import.meta.env.BASE_URL}landing/live-board.png`}
            width={1280}
            height={720}
            alt="Tablero en vivo de SpeedHack: arquitectura en Miro a la izquierda y tickets de Linear a la derecha, con la línea de nueve etapas arriba y el aviso de datos de demostración."
          />
          <figcaption>Captura real del tablero con una ejecución grabada.</figcaption>
        </figure>
      </section>

      <section className="landing__section">
        <SectionHeader title="Cómo funciona" meta="3 pasos, 9 estaciones" />
        <MetroLine current={9} />
        <ol className="landing__steps">
          {STEPS.map((s) => (
            <li key={s.n}>
              <span className="landing__n" aria-hidden="true">{s.n}</span>
              <div>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            </li>
          ))}
        </ol>
        <p className="landing__note">
          Tres aprobaciones humanas frenan la ejecución antes de avanzar: spec, diseño y calidad.
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
        <h2>Prueba una idea ahora</h2>
        <a className="sh-btn sh-btn--primary" href="#/intake">Probar la demo</a>
        <small>Hacktoberfest Hack Day CDMX (MLH), 27 y 28 de octubre de 2026. Los negocios y prospectos son ficticios.</small>
      </footer>
    </div>
  );
}
