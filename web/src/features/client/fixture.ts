// Local copy of app/fixtures/client/journey.json: the screen still works when the API is unreachable.
export type Journey = {
  demo_data: boolean;
  business: { name: string; owner: string; place: string; note: string };
  questions: { id: string; question: string; answer: string }[];
  summary: { headline: string; points: string[] };
  screens: { id: string; title: string; description: string }[];
  progress: { percent: number; steps: { id: string; title: string; state: "done" | "current" | "next" }[] };
  whatsapp: { to_name: string; message: string; opt_in: string; opt_out: string; sent: boolean };
  published_app: { url: string; note: string };
  audio_guide: {
    title: string;
    duration_seconds: number;
    src: string | null;
    recorded_path: string;
    recorded: boolean;
    note: string;
    transcript: string[];
  };
};

export const FALLBACK_JOURNEY: Journey = {
  demo_data: true,
  business: {
    name: "Barbería Don Chuy",
    owner: "Doña Lupe",
    place: "Colonia Escandón, Ciudad de México",
    note: "Negocio ficticio para la demostración.",
  },
  questions: [
    { id: "q1", question: "¿Qué quiere que haga su página?", answer: "Que mis clientes vean los precios y aparten su cita sin llamarme." },
    { id: "q2", question: "¿Qué servicios ofrece?", answer: "Corte de cabello, arreglo de barba y corte para niños." },
    { id: "q3", question: "¿Cuándo abre?", answer: "De martes a sábado, de 10 de la mañana a 7 de la noche." },
    { id: "q4", question: "¿Cómo quiere que le avisen de una cita?", answer: "Por WhatsApp, pero solo si el cliente acepta." },
  ],
  summary: {
    headline: "Una página sencilla para que le aparten cita.",
    points: [
      "Sus clientes ven sus tres servicios con el precio.",
      "Escogen día y hora libres, sin llamarle.",
      "A usted le llega un aviso por WhatsApp con cada cita nueva.",
    ],
  },
  screens: [
    { id: "s1", title: "Inicio", description: "Su nombre, su dirección y un botón grande: Apartar cita." },
    { id: "s2", title: "Servicios y precios", description: "Corte, barba y corte para niños, cada uno con su precio." },
    { id: "s3", title: "Elegir día y hora", description: "Un calendario con los horarios libres." },
    { id: "s4", title: "Cita confirmada", description: "Un mensaje que dice que su cita quedó apartada." },
  ],
  progress: {
    percent: 60,
    steps: [
      { id: "p1", title: "Entendimos su negocio", state: "done" },
      { id: "p2", title: "Dibujamos las pantallas", state: "done" },
      { id: "p3", title: "Armamos su página", state: "current" },
      { id: "p4", title: "Probamos que todo funcione", state: "next" },
      { id: "p5", title: "Publicamos su página", state: "next" },
    ],
  },
  whatsapp: {
    to_name: "Marco (cliente de ejemplo)",
    message: "Hola Marco, su cita en Barbería Don Chuy quedó apartada para el miércoles a las 5:00 de la tarde. Lo esperamos.",
    opt_in: "Marco aceptó recibir avisos de su cita por WhatsApp.",
    opt_out: "Para no recibir más avisos, responda BAJA en cualquier momento.",
    sent: false,
  },
  published_app: {
    url: "https://barberia-don-chuy.example.invalid",
    note: "Enlace de ejemplo: la página todavía no está publicada.",
  },
  audio_guide: {
    title: "Guía en audio para Doña Lupe",
    duration_seconds: 120,
    src: null,
    recorded_path: "app/fixtures/client/audio/guia-dona-lupe.mp3",
    recorded: false,
    note: "Audio pendiente de grabar. Mientras tanto, puede leer el texto o escucharlo con la voz de su navegador.",
    transcript: [
      "Hola, Doña Lupe. Le explico en dos minutos qué estamos haciendo.",
      "Usted nos contó que quiere que sus clientes vean los precios y aparten su cita sin llamarle.",
      "Por eso su página tendrá cuatro pantallas: el inicio, los servicios con precio, el calendario para elegir hora y un aviso de cita confirmada.",
      "Cuando alguien aparta una cita, a usted le llega un aviso por WhatsApp. Solo se lo mandamos a quien dijo que sí, y siempre puede pedir que no le escribamos más.",
      "Ahorita vamos en el 60 por ciento. Falta probar que todo funcione y publicarla.",
      "Cuando esté lista, le daremos un enlace para que lo comparta con sus clientes. Gracias por su confianza.",
    ],
  },
};
