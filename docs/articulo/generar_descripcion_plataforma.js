// Genera "Cómo funciona el Observatorio del mercado laboral en datos" (.docx) para el director del grupo.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber, TableOfContents, PageBreak,
} = require("docx");

const AZUL = "002D62", NARANJA = "D96500", GRIS = "5B6575", FONDO = "EEF3FA", FONDO_AVISO = "FFF4E5";
const ANCHO = 9360; // carta con márgenes de 1": 12240 - 2*1440

// Texto con **negrita** en línea
function runs(texto, extra = {}) {
  return texto.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((t) =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true, ...extra }) : new TextRun({ text: t, ...extra }));
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 140, line: 300 }, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const B = (t, nivel = 0) => new Paragraph({ numbering: { reference: "vinetas", level: nivel }, children: runs(t), spacing: { after: 80, line: 290 } });
const N = (t, ref) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 80, line: 290 } });

// Recuadro de una celda (para "En palabras sencillas" y avisos)
function recuadro(titulo, lineas, color = FONDO) {
  const borde = { style: BorderStyle.SINGLE, size: 4, color: color === FONDO ? "B8C7DD" : "F2C48D" };
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: [ANCHO],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: ANCHO, type: WidthType.DXA },
      shading: { fill: color, type: ShadingType.CLEAR, color: "auto" },
      borders: { top: borde, bottom: borde, left: borde, right: borde },
      margins: { top: 140, bottom: 140, left: 200, right: 200 },
      children: [
        new Paragraph({ keepNext: true, keepLines: true, children: [new TextRun({ text: titulo, bold: true, color: AZUL })], spacing: { after: 80 } }),
        ...lineas.map((l, i) => new Paragraph({ keepNext: i < lineas.length - 1, keepLines: true, children: runs(l), spacing: { after: 60, line: 280 } })),
      ],
    })] })],
  });
}

// Tabla con encabezado sombreado
function tabla(anchos, encabezado, filas) {
  const borde = { style: BorderStyle.SINGLE, size: 4, color: "C9D3E0" };
  const bordes = { top: borde, bottom: borde, left: borde, right: borde };
  const celda = (t, i, cab) => new TableCell({
    width: { size: anchos[i], type: WidthType.DXA }, borders: bordes,
    shading: cab ? { fill: AZUL, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: runs(t, cab ? { bold: true, color: "FFFFFF" } : {}), spacing: { after: 0, line: 270 } })],
  });
  return new Table({
    width: { size: anchos.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: anchos,
    rows: [new TableRow({ tableHeader: true, children: encabezado.map((t, i) => celda(t, i, true)) }),
           ...filas.map((f) => new TableRow({ cantSplit: true, children: f.map((t, i) => celda(t, i, false)) }))],
  });
}
const espacio = () => new Paragraph({ children: [], spacing: { after: 120 } });

const contenido = [
  // ---------------- Portada ----------------
  new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "Cómo funciona el Observatorio del mercado laboral en datos", bold: true, size: 44, color: AZUL, font: "Arial" })] }),
  new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: "Descripción de la plataforma, paso a paso, para el grupo de investigación", size: 28, color: GRIS })] }),
  new Paragraph({ children: [new TextRun({ text: "Juan Felipe Bernal · Data Scientist", bold: true, size: 24 })] }),
  new Paragraph({ children: [new TextRun({ text: "Versión del 7 de noviembre de 2026 · plataforma v0.13.1", size: 22, color: GRIS })] }),
  new Paragraph({ spacing: { after: 400 }, children: [new TextRun({ text: "Sitio: jfbernalp.dev · Tablero: superset.jfbernalp.dev · Código: github.com/jfbernalp/proyecto_investigativo", size: 20, color: GRIS })] }),
  recuadro("Para qué sirve este documento", [
    "Explica, con palabras sencillas, cómo la plataforma convierte avisos de empleo publicados en internet en información confiable, y cómo esa información alimenta a un modelo de inteligencia artificial que propone programas de formación.",
    "Es la base de la sección de descripción del sistema del primer artículo científico del proyecto: **diseño y evaluación de un observatorio auditable con inteligencia artificial generativa anclada en datos** (método: Design Science Research).",
    "Toda cifra de este documento sale de la plataforma y lleva su fecha de corte. Los ejemplos construidos para explicar un paso están marcados como **ejemplo ilustrativo**.",
  ]),
  new Paragraph({ children: [new PageBreak()] }),

  new Paragraph({ children: [new TextRun({ text: "Contenido", bold: true, size: 32, color: AZUL })], spacing: { after: 200 } }),
  new TableOfContents("Contenido", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),

  // ---------------- 1. Panorama ----------------
  H1("1. La idea en una página"),
  P("Cada mes miles de empresas publican vacantes en portales de empleo. Esos avisos dicen, en lenguaje libre, qué habilidades buscan, cuánta experiencia piden y, a veces, cuánto pagan. Juntos son un termómetro del mercado laboral, pero están dispersos, escritos de mil formas distintas y desaparecen cuando la vacante se cierra."),
  P("El observatorio hace cuatro cosas, de forma automática y repetible cada mes, para cuatro roles: **análisis de datos, ciencia de datos, ingeniería de datos y business intelligence (BI)**:"),
  N("**Recoge** los avisos de siete fuentes.", "pasos"),
  N("**Los ordena y limpia**: los convierte de texto libre en una ficha con campos comparables.", "pasos"),
  N("**Los guarda** en una base de datos que conserva el historial de todos los meses sin borrar nada.", "pasos"),
  N("**Los analiza y se los entrega a un modelo de inteligencia artificial**, que propone programas de formación usando solo cifras del observatorio. Un verificador revisa cada cifra antes de que una persona apruebe.", "pasos"),
  espacio(),
  tabla([1500, 3360, 4500], ["Paso", "Qué pasa", "Herramienta"], [
    ["1. Disparo", "Cada mes, un reloj programado arranca todo el proceso.", "GitHub Actions (servidor de automatización de GitHub)"],
    ["2. Recolección", "Se visitan los portales y se copian los avisos.", "Programas de \"web scraping\" en Python, uno por portal"],
    ["3. Limpieza", "Cada aviso se convierte en una ficha ordenada.", "Reglas de texto en Python (expresiones regulares)"],
    ["4. Almacenamiento", "Las fichas se guardan con su mes, sin borrar las anteriores.", "Base de datos relacional PostgreSQL (servicio Supabase)"],
    ["5. Análisis", "Se calculan demanda de habilidades y diferencias salariales.", "Estadística en Python (pandas, statsmodels) y tablero Apache Superset"],
    ["6. Inteligencia artificial", "Un modelo propone programas; un verificador revisa las cifras; una persona decide.", "Gemini 4 Argon (Google) + verificador propio + portal web"],
  ]),
  espacio(),
  recuadro("La regla de oro del observatorio", [
    "**No se inventan cifras.** Si un dato no existe o la muestra no alcanza, la respuesta correcta es «dato no disponible» o «no concluyente». Cada cifra se publica con su tamaño de muestra (n) y su fecha de corte. Esta regla guía todas las decisiones técnicas que se describen a continuación.",
  ]),

  // ---------------- 2. Disparo ----------------
  H1("2. Paso 1: el disparo automático cada mes"),
  P("Nadie tiene que acordarse de correr el observatorio. El código vive en GitHub, un servicio donde se guardan y versionan programas, que además ofrece **GitHub Actions**: una especie de alarma programada que arranca un computador en la nube y ejecuta una lista de tareas."),
  P("La alarma suena **el día 1 de cada mes a las 00:00 (hora universal)**, que en Colombia es el último día del mes a las 7:00 p. m. Ese computador temporal sigue siempre el mismo guion:"),
  N("Descarga la versión vigente del código e instala las herramientas necesarias.", "guion"),
  N("**Saca una copia de seguridad cifrada** de toda la base de datos antes de escribir nada. Si algo saliera mal, se puede volver al estado anterior.", "guion"),
  N("Ejecuta la recolección, la limpieza y el guardado (pasos 2 a 4 de este documento).", "guion"),
  N("Recalcula el análisis de diferencias salariales con los datos del nuevo mes.", "guion"),
  N("Guarda los archivos del mes como evidencia descargable durante 90 días.", "guion"),
  P("Si un paso falla, el proceso se detiene y queda registrado; no se escriben datos a medias. El corte de noviembre de 2026 (1 de noviembre) corrió completo en 14 minutos."),
  recuadro("En palabras sencillas", ["Es como un empleado muy disciplinado que, el último día de cada mes, hace una copia de los archivos, sale a recoger los avisos de empleo, los ordena, los archiva y actualiza los informes, siempre en el mismo orden y dejando constancia de lo que hizo."]),

  // ---------------- 3. Recolección ----------------
  H1("3. Paso 2: la recolección de avisos (web scraping)"),
  P("**Web scraping** es usar un programa para leer páginas web y copiar de ellas la información que interesa, como lo haría una persona con el navegador, pero de forma automática. Para cada portal hay un programa (\"scraper\") que sabe cómo está organizada esa página."),
  H2("3.1 Las fuentes"),
  tabla([2600, 6760], ["Fuente", "Qué aporta"], [
    ["CompuTrabajo, ElEmpleo, Magneto", "Portales colombianos; son los que más publican el salario."],
    ["LinkedIn, Talent.com", "Gran volumen de vacantes; casi nunca publican salario."],
    ["Get on Board", "Portal latinoamericano de empleos tecnológicos, muchos remotos."],
    ["Remotive", "Empleos remotos internacionales, a través de su servicio público de datos (API), que exige citar la fuente."],
  ]),
  espacio(),
  P("Hubo dos fuentes que se dejaron de usar: Torre.ai, porque cambió su servicio en octubre de 2026 (solo hay datos de septiembre), y Glassdoor, porque su sitio bloquea la lectura automática y sus reglas públicas (el archivo robots.txt) la prohíben."),
  H2("3.2 Cómo trabaja un scraper"),
  B("Busca los términos del rol en el portal, por ejemplo «científico de datos», «data scientist», «analista de datos» o «ingeniero de datos», con ubicación Colombia."),
  B("Recorre las páginas de resultados (hasta cinco por portal en el corte mensual)."),
  B("De cada aviso copia: título, empresa, ubicación, salario tal como aparece escrito, requisitos, descripción completa, fecha y el código que el portal le asigna."),
  B("Si el portal no responde, espera y reintenta tres veces (a los 10, 30 y 60 segundos) antes de darse por vencido."),
  B("Al final emite un **reporte de salud**: avisa si un portal no trajo nada o trajo menos de la mitad que el mes anterior."),
  P("Todo lo recolectado se guarda primero **tal cual llegó** (el «crudo»), junto con su mes. Así, si más adelante se mejora una regla de limpieza, se puede volver a procesar el texto original de cualquier mes sin tener que volver a visitar los portales."),
  recuadro("Un punto delicado: los términos de búsqueda", [
    "La muestra depende de **qué se busca**. El 17 de octubre de 2026 se amplió la búsqueda en LinkedIn: antes solo buscaba «científico de datos», después también «analista de datos» e «ingeniero de datos». Al comparar septiembre con octubre parecía que el rol «Ingeniero de Datos» crecía mucho, pero era el efecto del cambio de búsqueda, no del mercado. Desde entonces, las comparaciones entre meses excluyen las fuentes cuyos términos cambiaron.",
  ], FONDO_AVISO),

  // ---------------- 4. Limpieza ----------------
  H1("4. Paso 3: limpieza y transformación (de texto libre a ficha ordenada)"),
  P("Esta es la parte que convierte un aviso escrito libremente en datos que se pueden contar y comparar. En inglés se le llama «parsing» o procesamiento. La idea es simple: un aviso es como una carta escrita a mano, y lo que necesitamos es un **formulario con casillas**, todas llenadas con el mismo criterio para todos los avisos."),
  P("El trabajo lo hacen **reglas de texto**: instrucciones del tipo «si el aviso contiene la palabra SQL o PostgreSQL, marque la casilla SQL». Técnicamente se escriben como «expresiones regulares», un lenguaje para describir patrones de texto. No se usa inteligencia artificial en este paso: las reglas son explícitas, revisables y dan siempre el mismo resultado para el mismo texto."),
  H2("4.1 Un ejemplo de principio a fin"),
  P("**Ejemplo ilustrativo** (aviso inventado para explicar el proceso; no es una oferta real):"),
  recuadro("Aviso tal como llega del portal", [
    "**Título:** Analista de Datos Senior — Bogotá",
    "**Salario:** $5 a $6 millones",
    "**Requisitos:** Profesional en ingeniería o estadística. Mínimo 4 años de experiencia. Manejo de SQL Server, Python y Power BI. Inglés intermedio.",
  ]),
  espacio(),
  tabla([3000, 6360], ["Casilla de la ficha", "Cómo se llena en el ejemplo"], [
    ["Identificador único", "Una «huella digital» calculada con el nombre del portal y el código del aviso. El mismo aviso siempre produce la misma huella."],
    ["¿Es del tema?", "Sí: el título contiene «datos»."],
    ["Rol", "Analista de Datos: el título contiene «analista de datos»."],
    ["Años de experiencia", "4: el texto dice «mínimo 4 años»."],
    ["Nivel", "Senior, con fuente «años explícitos»."],
    ["Habilidades", "SQL (por «SQL Server»), Python, Power BI."],
    ["Salario mensual (COP)", "5.500.000: punto medio del rango «$5 a $6 millones»."],
    ["Mercado", "Local (Colombia, pesos)."],
    ["Mes", "202611 (noviembre de 2026)."],
  ]),
  espacio(),
  H2("4.2 Los pasos, uno por uno"),
  H3("a) Saneamiento técnico"),
  P("Se eliminan caracteres invisibles que dañan los archivos y se neutraliza cualquier texto que empiece como fórmula de Excel (por ejemplo «=…»), para que abrir los archivos exportados no pueda ejecutar nada indeseado."),
  H3("b) Identificador único y duplicados"),
  P("A cada aviso se le calcula una huella digital (con el algoritmo SHA-256) a partir del portal y del código que el portal le asigna. Si el mismo aviso aparece en dos corridas del mismo mes, la base de datos reconoce la huella y no lo guarda dos veces. Si reaparece al mes siguiente, se registra como «visto de nuevo», lo que permite saber qué vacantes son nuevas y cuáles siguen abiertas."),
  H3("c) Filtro de relevancia"),
  P("Los portales devuelven avisos que no tienen que ver con datos (por ejemplo, de enfermería o ventas). Se conservan solo los que tienen en el título palabras del tema (datos, data, BI, machine learning, estadística, SQL, Python…) y no tienen palabras de exclusión."),
  H3("d) Clasificación del rol"),
  P("El rol se decide por el **título** del aviso, no por el término que se buscó, porque una búsqueda de «científico de datos» trae también analistas e ingenieros. Hay seis grupos: Científico de Datos, Analista de Datos, Ingeniero de Datos, Machine Learning / AI Engineer, Analista de BI y Desarrollador. Ver la limitación de este paso en la sección 8."),
  H3("e) Experiencia y nivel"),
  P("Se buscan frases como «mínimo 3 años», «de 2 a 4 años», «sin experiencia» o «5+ years». Por la regla de oro, **si el aviso no lo dice, la casilla queda vacía**: antes de octubre de 2026 el sistema asumía «1 año» cuando no encontraba el dato, y eso se corrigió. El nivel (Junior, Semi-Senior, Senior, Líder) se toma de los años, o del título solo si dice explícitamente «senior», «junior», etc., y cada ficha guarda de dónde salió el dato."),
  H3("f) Habilidades"),
  P("Se usa una **taxonomía** (un catálogo controlado) de **31 habilidades** agrupadas en 5 categorías: lenguajes, BI y visualización, big data y nube, machine learning e IA, e ingeniería de datos y operaciones. Cada habilidad tiene su patrón. Por ejemplo, «SQL» se reconoce por sql, PostgreSQL, MySQL, Oracle, SQL Server o PL/SQL. Los patrones buscan palabras completas, para que «NoSQL» no cuente como «SQL», un error que se encontró y se corrigió en octubre de 2026."),
  H3("g) Salario"),
  P("El salario llega escrito de muchas formas y se convierte a **pesos colombianos por mes**:"),
  B("Un rango («$3.000.000 a $4.000.000») se convierte en su punto medio."),
  B("«$2,5 a $3 millones» se interpreta como millones."),
  B("Un valor por hora se multiplica por 160 horas al mes; uno anual se divide entre 12."),
  B("Las monedas extranjeras se convierten con tasas fijas de referencia (1 dólar = 4.000 pesos)."),
  B("«A convenir» o «confidencial» quedan como dato faltante, nunca como cero."),
  H3("h) Mercado local o internacional"),
  P("Es internacional si el salario está en moneda extranjera o si la fuente es un portal de trabajo remoto internacional. El resto es local. Antes de octubre de 2026 una regla mal escrita marcaba como internacionales avisos sin salario; se corrigió y se reclasificaron 559 avisos."),
  H3("i) Formato «largo»"),
  P("Al final, cada aviso queda como una ficha, y además se genera una fila por cada par «aviso–habilidad». Este formato facilita contar cuántos avisos piden cada habilidad cada mes."),
  recuadro("En palabras sencillas", ["La limpieza es un equipo de digitadores que lee cada aviso y llena el mismo formulario, siempre con las mismas reglas y sin adivinar. Solo que son reglas escritas en un programa, por lo que se pueden revisar, corregir y volver a aplicar a todos los meses."]),

  // ---------------- 5. Almacenamiento ----------------
  H1("5. Paso 4: almacenamiento en una base de datos relacional"),
  P("Una **base de datos relacional** guarda la información en tablas (como hojas de cálculo) que se conectan entre sí por un identificador común; aquí, la huella digital de cada aviso. Se usa PostgreSQL, un motor de base de datos de uso científico e industrial, alojado en el servicio Supabase."),
  tabla([3100, 6260], ["Tabla", "Qué guarda"], [
    ["Avisos (dim_ofertas)", "Una fila por aviso único: portal, título, empresa, rol, mercado y fecha en que se vio por primera vez."],
    ["Extracciones por mes (fact_extracciones_historico)", "Una fila por aviso y mes en que se vio: salario, experiencia, nivel y su fuente."],
    ["Habilidades por mes (fact_habilidades_historico)", "Una fila por aviso, habilidad y mes."],
    ["Texto original (ofertas_raw_historico)", "El aviso completo tal como llegó, por mes, para poder reprocesarlo."],
    ["Resultados del análisis (analisis_primas_*)", "Las diferencias salariales calculadas en cada corte, con sus intervalos."],
  ]),
  espacio(),
  H2("5.1 Protecciones del historial"),
  B("**Solo se agrega, nunca se borra ni se modifica**: la base rechaza automáticamente cualquier intento de borrar o cambiar el historial. Correcciones excepcionales requieren un modo de mantenimiento explícito."),
  B("**No hay duplicados**: la base no admite dos veces el mismo aviso en el mismo mes."),
  B("**Permisos mínimos**: el proceso automático entra con un usuario que solo puede leer y agregar; no puede borrar ni cambiar la estructura."),
  B("**Copia cifrada antes de cada corte**, guardada como evidencia del proceso."),
  H2("5.2 Del almacenamiento a lo que se ve"),
  P("Sobre las tablas se definen **vistas**, que son consultas guardadas que entregan los datos ya listos para mostrar: avisos por mes, demanda de habilidades, salarios. El tablero público (Apache Superset) y la página web leen esas mismas vistas, así que todos ven las mismas cifras. El tablero se actualiza en menos de 5 minutos después de cada corte."),
  P("Estado al corte del 1 de noviembre de 2026: **907 vacantes únicas** registradas entre septiembre y noviembre; en noviembre, **382 avisos** de 7 fuentes, de los cuales el **27,5 % publica salario**."),

  // ---------------- 6. Análisis ----------------
  H1("6. Paso 5: el análisis estadístico (resumen)"),
  P("Con los datos ordenados se calculan dos tipos de resultados:"),
  B("**Demanda**: qué porcentaje de los avisos de cada mes pide cada habilidad. En noviembre de 2026 lideran SQL (68,1 %), Python (63,9 %) y ETL / pipelines de datos (51,6 %)."),
  B("**Primas salariales**: entre avisos comparables (mismo nivel, rol, portal y mes), cuánto más o menos ofrecen los que piden una habilidad. Se usa una regresión sobre el logaritmo del salario, con errores robustos, intervalos de confianza del 95 % y corrección por comparar muchas habilidades a la vez (Benjamini–Hochberg). Un resultado se declara **concluyente** solo si su intervalo no incluye el cero y pasa la corrección."),
  P("Resultados preliminares (corte 2026-11-01, 176 avisos locales con salario): los Analistas de Datos reciben ofertas **35,3 % menores** que los Científicos de Datos (intervalo de −45,0 % a −24,0 %); la habilidad Excel Avanzado se asocia con ofertas **17,0 % menores** (de −27,1 % a −5,5 %); ninguna habilidad muestra todavía una prima positiva concluyente. Son asociaciones, no efectos causales, y la clasificación de rol tiene una limitación descrita en la sección 8."),

  // ---------------- 7. IA ----------------
  H1("7. Paso 6: el envío al modelo de inteligencia artificial"),
  P("La última etapa usa un **modelo de lenguaje** (LLM, el mismo tipo de tecnología que ChatGPT) para proponer programas de formación: electivas, microcredenciales, especializaciones y maestrías. El riesgo conocido de estos modelos es que **inventan cifras con seguridad**. Todo el diseño de esta etapa busca evitarlo y, cuando no se logra, hacerlo visible."),
  H2("7.1 El «contexto»: lo que el modelo puede usar"),
  P("Antes de llamar al modelo, el sistema arma un paquete de datos llamado **contexto de mercado**, tomado de la misma base que el tablero. Incluye la demanda de cada habilidad con su n, los roles con su perfil de habilidades, las primas salariales con sus intervalos y una lista de limitaciones. El paquete se guarda con un identificador único, de modo que siempre se sabe con qué datos se generó cada propuesta."),
  H2("7.2 Las instrucciones"),
  P("Junto al contexto, el modelo recibe reglas explícitas: copiar las cifras tal como aparecen en el contexto, citando su n y su fecha; escribir «dato no disponible en el observatorio» cuando falte un dato; usar como argumento salarial solo las primas concluyentes; no proponer precios; y respetar la equivalencia del Decreto 1330 (1 crédito = 48 horas: 16 con docente y 32 de trabajo independiente). La evidencia se ordena por fuerza: primero la demanda, luego los roles, luego las primas concluyentes y al final lo no concluyente."),
  H2("7.3 El modelo"),
  P("Se usa **Gemini 4 Argon** de Google. Se eligió tras una prueba comparativa: refinando la misma maestría, el modelo anterior (Gemini Flash) declaró 48 créditos con módulos que sumaban 16, mientras que Argon cuadró los 48. Cada versión de una propuesta registra qué modelo la redactó."),
  H2("7.4 El verificador de cifras"),
  P("Cuando el modelo responde, un programa propio revisa automáticamente cada cifra del texto:"),
  N("**Existencia**: ¿el porcentaje, monto o número de avisos aparece en el contexto?", "verif"),
  N("**Atribución**: ¿está asignado a la habilidad o rol correcto? (por ejemplo, que no le atribuya a AWS el porcentaje de ETL).", "verif"),
  N("**Consistencia**: ¿los créditos de los módulos suman el total y las horas corresponden a los créditos?", "verif"),
  N("**Tarifas**: cualquier precio se marca, porque el observatorio no tiene datos de tarifas.", "verif"),
  P("Las cifras que fallan se muestran en rojo a quien aprueba. El verificador **marca, no bloquea**: la decisión final es humana."),
  H2("7.5 La revisión humana"),
  P("En el portal, el rol aprobador puede aprobar (se congela el documento final en formato institucional), rechazar con un motivo, o pedir ajustes a la IA con comentarios; cada versión vuelve a pasar por el verificador. Todas las acciones quedan en un registro de auditoría."),
  recuadro("Evidencia que se evaluará en el artículo", [
    "Antes de existir el contexto verificado, las propuestas tenían entre 11 y 15 cifras sin respaldo cada una (salarios inventados, porcentajes inexistentes, tarifas). Tras regenerarlas con el contexto, las reglas y el verificador, las cinco propuestas vigentes no tienen cifras marcadas (revisión del 28 de octubre de 2026).",
    "El artículo medirá esto de forma sistemática: tasa de cifras sin respaldo, errores de atribución, consistencia de créditos y comparación entre modelos.",
  ]),

  // ---------------- 8. Limitaciones ----------------
  H1("8. Limitaciones conocidas"),
  P("Un observatorio confiable declara sus límites. Estos son los vigentes y forman parte del artículo:"),
  B("**Muestra salarial pequeña y seleccionada.** Solo el 27,5 % de los avisos de noviembre publica salario, y casi todos vienen de tres portales colombianos. Las primas describen ese grupo, no todo el mercado."),
  B("**La muestra depende de los términos de búsqueda.** El caso de LinkedIn (sección 3) lo muestra; los cambios de búsqueda quedan registrados y se excluyen al comparar meses."),
  B("**Pocos meses.** Con tres cortes (septiembre a noviembre de 2026) no se puede hablar de tendencias. Además, octubre acumuló varias corridas y noviembre una sola, así que sus conteos no son directamente comparables."),
  B("**Tasas de cambio fijas** para salarios en moneda extranjera."),
  B("**Precisión de las reglas sin medir.** La detección de experiencia se revisó a mano (12 de 12 casos correctos), pero la de habilidades todavía no se ha comparado contra una muestra etiquetada por personas. Está planificado."),
  B("**Clasificación de rol (encontrada al preparar este documento).** Las reglas del rol buscan fragmentos de texto en lugar de palabras completas, y los títulos que no coinciden con ninguna regla quedan por defecto como «Científico de Datos». De 905 avisos únicos, 212 (23 %) quedan en ese grupo por defecto, y 152 (17 %) cambiarían de rol si las reglas exigieran palabras completas; por ejemplo, «Specialist» o «Chía» se clasifican como «Machine Learning / AI Engineer» porque contienen las letras «ia». Esto afecta la comparación entre roles y debe corregirse antes de publicar esos resultados."),
  B("**Términos de uso de los portales.** Está pendiente una revisión ética y legal de la recolección, sobre todo para LinkedIn. De ella depende qué datos se pueden compartir abiertamente (probablemente solo agregados)."),

  // ---------------- 9. Glosario ----------------
  H1("9. Glosario"),
  tabla([2600, 6760], ["Término", "Significado"], [
    ["API", "Puerta de acceso que un servicio ofrece para que otros programas pidan datos de forma ordenada."],
    ["Base de datos relacional", "Tablas conectadas entre sí por identificadores comunes."],
    ["Corte", "Cada recolección mensual; se identifica por su fecha (por ejemplo, 2026-11-01)."],
    ["Expresión regular", "Forma de describir patrones de texto («la palabra SQL o PostgreSQL»)."],
    ["GitHub Actions", "Servicio que ejecuta tareas programadas en computadores de GitHub."],
    ["Intervalo de confianza", "Rango de valores compatibles con los datos; si incluye el cero, no se puede afirmar que exista diferencia."],
    ["LLM", "Modelo de lenguaje de gran tamaño, el tipo de inteligencia artificial que genera texto."],
    ["n", "Tamaño de muestra: cuántos avisos respaldan una cifra."],
    ["Prima salarial", "Diferencia porcentual de salario ofrecido entre avisos comparables con y sin una característica."],
    ["Taxonomía", "Catálogo controlado de habilidades con sus formas de escribirse."],
    ["Web scraping", "Lectura automática de páginas web para copiar información."],
  ]),
];

const doc = new Document({
  creator: "Juan Felipe Bernal", title: "Cómo funciona el Observatorio del mercado laboral en datos",
  description: "Descripción de la plataforma para el grupo de investigación",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: AZUL }, paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: AZUL }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: "Arial", color: NARANJA }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "vinetas", levels: [
      { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
      { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } } ] },
    ...["pasos", "guion", "verif"].map((ref) => ({ reference: ref, levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } } ] })),
  ] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Observatorio del mercado laboral en datos · ", color: GRIS, size: 18 }),
      new TextRun({ children: [PageNumber.CURRENT], color: GRIS, size: 18 }) ] })] }) },
    children: contenido,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const salida = process.argv[2];
  fs.writeFileSync(salida, buf);
  console.log("escrito", salida, buf.length, "bytes");
});
