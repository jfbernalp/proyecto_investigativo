// Genera la guía de anotación en Word para las personas anotadoras (contenido de guia_anotacion.md, adaptado).
// Uso: NODE_PATH=<carpeta con node_modules de docx> node generar_guia_anotacion.js salida.docx
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber, PageBreak,
} = require("docx");

const AZUL = "002D62", NARANJA = "D96500", GRIS = "5B6575", FONDO = "EEF3FA", FONDO_AVISO = "FFF4E5";
const ANCHO = 9360;

function runs(texto, extra = {}) {
  return texto.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((t) =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true, ...extra }) : new TextRun({ text: t, ...extra }));
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 140, line: 300 }, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const B = (t) => new Paragraph({ numbering: { reference: "vinetas", level: 0 }, children: runs(t), spacing: { after: 80, line: 290 } });
const N = (t, ref) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 80, line: 290 } });
const espacio = () => new Paragraph({ children: [], spacing: { after: 120 } });

function recuadro(titulo, lineas, color = FONDO) {
  const borde = { style: BorderStyle.SINGLE, size: 4, color: color === FONDO ? "B8C7DD" : "F2C48D" };
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: [ANCHO],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: ANCHO, type: WidthType.DXA }, shading: { fill: color, type: ShadingType.CLEAR, color: "auto" },
      borders: { top: borde, bottom: borde, left: borde, right: borde }, margins: { top: 140, bottom: 140, left: 200, right: 200 },
      children: [
        new Paragraph({ keepNext: true, children: [new TextRun({ text: titulo, bold: true, color: AZUL })], spacing: { after: 80 } }),
        ...lineas.map((l, i) => new Paragraph({ keepNext: i < lineas.length - 1, children: runs(l), spacing: { after: 60, line: 280 } })),
      ],
    })] })],
  });
}

function tabla(anchos, encabezado, filas) {
  const borde = { style: BorderStyle.SINGLE, size: 4, color: "C9D3E0" };
  const bordes = { top: borde, bottom: borde, left: borde, right: borde };
  const celda = (t, i, cab) => new TableCell({
    width: { size: anchos[i], type: WidthType.DXA }, borders: bordes,
    shading: cab ? { fill: AZUL, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [new Paragraph({ children: runs(t, cab ? { bold: true, color: "FFFFFF" } : {}), spacing: { after: 0, line: 260 } })],
  });
  return new Table({
    width: { size: anchos.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: anchos,
    rows: [new TableRow({ tableHeader: true, children: encabezado.map((t, i) => celda(t, i, true)) }),
           ...filas.map((f) => new TableRow({ cantSplit: true, children: f.map((t, i) => celda(t, i, false)) }))],
  });
}

const HABILIDADES = [
  ["Python", "Se pide programar en Python.", "—"],
  ["R", "Se pide el lenguaje R o RStudio.", "«R&D», «R+D» o una letra R suelta con otro sentido **no** cuentan."],
  ["SQL", "Se pide SQL o una base de datos relacional (PostgreSQL, MySQL, SQL Server, Oracle **como base de datos**).", "**Oracle como ERP o sistema contable no cuenta.** «NoSQL» no cuenta aquí: va en «Bases de Datos NoSQL»."],
  ["Scala", "Lenguaje Scala.", "—"],
  ["Java / C++", "Java, C++ o C#.", "«JavaScript» **no** cuenta."],
  ["Power BI", "Power BI o DAX.", "—"],
  ["Tableau", "Tableau.", "—"],
  ["Excel u hojas de cálculo (cualquier nivel)", "Se pide Excel u hojas de cálculo, a cualquier nivel.", "Si además dice «avanzado», tablas dinámicas, macros o VBA, marque **también** la columna «Excel AVANZADO»."],
  ["Looker", "Looker o Looker Studio (antes Data Studio).", "—"],
  ["Qlik", "QlikView o Qlik Sense.", "—"],
  ["Spark / PySpark", "Apache Spark o PySpark.", "—"],
  ["Databricks", "Databricks.", "—"],
  ["Hadoop / Hive", "Hadoop o Hive.", "—"],
  ["Kafka", "Apache Kafka.", "—"],
  ["AWS", "Amazon Web Services o sus servicios (S3, EC2, Redshift, Glue, SageMaker…).", "—"],
  ["Azure", "Microsoft Azure o sus servicios (Synapse, Data Factory, Azure ML…).", "«Microsoft» u «Office 365» solos **no** cuentan."],
  ["Google Cloud (GCP)", "Google Cloud o sus servicios (BigQuery, Vertex AI…).", "«Google Analytics» o «Google Sheets» **no** cuentan."],
  ["Machine Learning General", "Aprendizaje automático o modelos predictivos en general.", "Una sigla «ML» que no se refiera a machine learning no cuenta."],
  ["Deep Learning", "Aprendizaje profundo o redes neuronales.", "—"],
  ["NLP / LLMs", "Procesamiento de lenguaje natural, LLM, GPT, BERT, transformers.", "«Transformers» en otro sentido (por ejemplo, eléctrico) no cuenta."],
  ["Computer Vision", "Visión por computador u OpenCV.", "—"],
  ["Scikit-Learn", "scikit-learn.", "—"],
  ["TensorFlow / Keras", "TensorFlow o Keras.", "—"],
  ["PyTorch", "PyTorch.", "—"],
  ["Estadística / Modelamiento", "Estadística, modelamiento estadístico, series de tiempo, inferencia.", "«Estadísticas» como sinónimo de reportes o cifras del negocio **no** cuenta si no se pide la disciplina."],
  ["ETL / Pipelines de Datos", "Procesos ETL/ELT o canalizaciones de datos (incluye dbt o Airbyte).", "**Un «pipeline» de ventas o de integración continua (CI/CD) de software no cuenta.**"],
  ["Airflow", "Apache Airflow.", "—"],
  ["Docker / Kubernetes", "Docker, Kubernetes o contenedores.", "—"],
  ["Git / Control de Versiones", "Git, GitHub, GitLab o control de versiones.", "—"],
  ["Bases de Datos NoSQL", "MongoDB, Cassandra, Redis, Elasticsearch o «NoSQL».", "—"],
  ["MLOps", "MLOps o MLflow.", "—"],
];

const contenido = [
  new Paragraph({ spacing: { before: 2000, after: 200 }, children: [new TextRun({ text: "Guía de anotación de ofertas de empleo", bold: true, size: 44, color: AZUL })] }),
  new Paragraph({ spacing: { after: 500 }, children: [new TextRun({ text: "Instrucciones para las personas anotadoras del Observatorio del mercado laboral en datos", size: 28, color: GRIS })] }),
  new Paragraph({ children: [new TextRun({ text: "Proyecto de Juan Felipe Bernal · Data Scientist", bold: true, size: 24 })] }),
  new Paragraph({ spacing: { after: 400 }, children: [new TextRun({ text: "Versión 1 · 7 de noviembre de 2026", size: 22, color: GRIS })] }),
  recuadro("En una frase", [
    "Usted va a leer ofertas de empleo reales y, para cada una, va a marcar **qué rol describe, cuánta experiencia pide, qué nivel tiene y qué habilidades técnicas solicita**. Sus respuestas serán la «respuesta correcta» contra la que se medirá qué tan bien acierta el sistema automático del observatorio.",
  ]),
  espacio(),
  tabla([3000, 6360], ["Quién", "Carga de trabajo"], [
    ["Persona anotadora A", "200 ofertas · unas 10 horas"],
    ["Persona anotadora B", "60 ofertas · unas 3 horas"],
    ["Ritmo recomendado", "Sesiones de 30 a 45 minutos; unos 3 minutos por oferta"],
    ["Archivo", "Una planilla de Excel con una oferta por fila"],
  ]),
  new Paragraph({ children: [new PageBreak()] }),

  H1("1. Por qué su trabajo es importante"),
  P("El observatorio lee automáticamente miles de ofertas de empleo y detecta en ellas habilidades como SQL, Python o Power BI. Para saber si lo hace bien, necesitamos un grupo de ofertas revisadas **por personas**, con criterio. Comparando lo que dice el sistema con lo que dicen ustedes calcularemos qué tanto acierta (precisión), qué tanto se le escapa (exhaustividad o *recall*) y en qué casos se equivoca."),
  P("Por eso es clave que **sus respuestas reflejen su propio juicio**: la planilla no muestra lo que detectó el sistema, a propósito."),

  H1("2. Reglas generales"),
  N("**Trabaje solo.** No consulte a la otra persona anotadora hasta terminar. Si dos personas etiquetan la misma oferta, necesitamos saber si llegan por separado a la misma respuesta.", "reglas"),
  N("**Juzgue por el significado, no por palabras sueltas.** El sistema busca palabras; usted decide si la oferta realmente pide esa habilidad. La sección 5 explica los casos difíciles.", "reglas"),
  N("**Solo cuenta lo que se pide para el cargo.** Requisitos, funciones, «deseable» o «valoramos» cuentan. No cuenta lo que describe a la empresa («somos líderes en inteligencia artificial») si no es parte del trabajo.", "reglas"),
  N("**Si duda, decida igual y explíquelo** en la columna «comentario». Las dudas nos ayudan a mejorar esta guía.", "reglas"),
  N("**No modifique las columnas grises** (id, portal, mes, título y texto). En el texto, [CORREO] y [TELÉFONO] reemplazan datos de contacto.", "reglas"),

  H1("3. Cómo llenar cada columna"),
  tabla([2600, 6760], ["Columna", "Qué escribir"], [
    ["rol", "Elija uno de la lista (sección 4), según el trabajo descrito **en conjunto** (título más funciones), no solo el título."],
    ["anios_minimos", "Años mínimos de experiencia **si la oferta los dice**: «de 2 a 4 años» → 2; «5+ años» → 5; «sin experiencia» → 0; «6 meses» → 0,5. Si la oferta no lo dice, **deje la celda vacía**: no adivine."],
    ["nivel", "Junior, Semi-Senior, Senior, Líder o «No se indica». Use lo que diga la oferta (en el título o el texto). Si solo hay años: 0–1 Junior, 2–3 Semi-Senior, 4–5 Senior, más de 5 Líder. Si no hay ninguna señal: «No se indica»."],
    ["Columnas de habilidades (amarillas)", "Escriba **1** si la oferta pide esa habilidad. Si no, deje la celda vacía."],
    ["Excel AVANZADO (lo dice explícitamente)", "1 solo si la oferta dice «Excel avanzado», tablas dinámicas, macros o VBA."],
    ["otras_habilidades", "Habilidades **técnicas** importantes que no tienen columna (por ejemplo SAS, SPSS, Snowflake, Jira), separadas por punto y coma."],
    ["comentario", "Dudas, casos raros, ofertas en otro idioma o con el texto incompleto."],
  ]),
  espacio(),
  recuadro("Consejo práctico", [
    "Lea primero el título y las funciones, decida el rol, y después recorra las columnas de habilidades de izquierda a derecha buscando cada una en el texto. Las listas desplegables de rol y nivel evitan errores de escritura.",
  ]),

  H1("4. Los roles"),
  tabla([2900, 6460], ["Rol", "Cuándo elegirlo"], [
    ["Científico de Datos", "Modelos estadísticos o de aprendizaje automático para predecir o explicar; experimentación."],
    ["Analista de Datos", "Consultas, limpieza, reportes y análisis descriptivo para responder preguntas del negocio."],
    ["Ingeniero de Datos", "Canalizaciones de datos, almacenamiento, bodegas y lagos de datos, plataformas; también arquitecto de datos y administrador de bases de datos."],
    ["Machine Learning / AI Engineer", "Llevar modelos a producción, MLOps, sistemas de IA o de modelos de lenguaje como producto."],
    ["Analista de BI y Visualización", "Tableros, indicadores, Power BI o Tableau como función principal."],
    ["Desarrollador de Software / Datos", "Desarrollo de software donde los datos son secundarios."],
    ["Otro rol", "Del tema de datos, pero ninguno de los anteriores (por ejemplo, gobierno de datos o gerente de analítica sin función técnica)."],
    ["No es del tema", "Nada que ver con datos (ventas, salud asistencial, etc.). En ese caso no hace falta marcar habilidades."],
  ]),
  espacio(),
  P("Si un cargo mezcla dos roles, elija el que ocupa **la mayor parte de las funciones** y anote el otro en el comentario."),

  H1("5. Las habilidades: qué cuenta y casos difíciles"),
  tabla([2300, 3530, 3530], ["Habilidad", "Marque 1 si…", "Casos difíciles"], HABILIDADES),

  new Paragraph({ children: [new PageBreak()] }),
  H1("6. Dos ejemplos resueltos"),
  P("Los dos avisos siguientes son **inventados** para explicar la guía; no son ofertas reales."),
  recuadro("Ejemplo 1 · el aviso", [
    "**Título:** Analista de Datos Senior",
    "**Texto:** Buscamos profesional con mínimo 4 años de experiencia. Funciones: construir reportes en Power BI, escribir consultas en SQL Server y automatizar procesos en Python. Deseable manejo de Excel avanzado (tablas dinámicas). Somos una empresa líder en inteligencia artificial para el sector financiero.",
  ]),
  espacio(),
  tabla([3000, 6360], ["Columna", "Respuesta y por qué"], [
    ["rol", "Analista de Datos: reportes, consultas y automatización para el negocio."],
    ["anios_minimos", "4 («mínimo 4 años»)."],
    ["nivel", "Senior (lo dice el título)."],
    ["Habilidades", "Power BI, SQL, Python, Excel (cualquier nivel) y Excel AVANZADO (dice «avanzado» y «tablas dinámicas»)."],
    ["Lo que NO se marca", "Machine Learning: «líder en inteligencia artificial» describe a la empresa, no el cargo."],
  ]),
  espacio(),
  recuadro("Ejemplo 2 · el aviso", [
    "**Título:** Ingeniero de Datos",
    "**Texto:** Diseñarás pipelines de datos en Azure Data Factory y Databricks, con control de versiones en Git. Conocimiento del ERP Oracle es un plus. Participarás en el pipeline comercial del área de ventas.",
  ]),
  espacio(),
  tabla([3000, 6360], ["Columna", "Respuesta y por qué"], [
    ["rol", "Ingeniero de Datos."],
    ["anios_minimos", "Vacío: no dice años."],
    ["nivel", "No se indica."],
    ["Habilidades", "ETL / Pipelines de Datos, Azure, Databricks, Git."],
    ["Lo que NO se marca", "SQL: Oracle aparece como ERP, no como base de datos. Y el «pipeline comercial» de ventas no es un pipeline de datos (la habilidad ya está marcada por la primera frase)."],
  ]),

  H1("7. Preguntas frecuentes"),
  B("**La oferta está en inglés.** Anótela igual, con los mismos criterios."),
  B("**El texto está cortado o casi vacío.** Anote lo que pueda con el título y escriba «texto incompleto» en el comentario."),
  B("**Pide «conocimientos en bases de datos» sin decir cuál.** No marque SQL ni NoSQL; anótelo en el comentario."),
  B("**Menciona una herramienta que no tiene columna.** Escríbala en «otras_habilidades» si es técnica."),
  B("**No estoy seguro del rol.** Elija el más cercano según las funciones y explique la duda en el comentario."),

  H1("8. Antes de entregar"),
  N("Todas las filas tienen rol y nivel.", "lista"),
  N("Las celdas de habilidades solo tienen 1 o están vacías (sin «x», «sí» ni ceros).", "lista"),
  N("Los años son números (use coma para decimales: 0,5).", "lista"),
  N("No modificó las columnas grises ni el orden de las filas.", "lista"),
  N("Guarde el archivo con su letra (A o B) en el nombre y envíelo a Juan Felipe Bernal.", "lista"),
  espacio(),
  recuadro("Qué pasa después", [
    "En las 60 ofertas que etiquetan las dos personas se mide el acuerdo entre ustedes. Las diferencias se resuelven conversando con esta guía en la mano; si la guía no cubría un caso, se actualiza. Con la versión final se evalúa el sistema del observatorio. **Gracias por su trabajo.**",
  ], FONDO_AVISO),
];

const doc = new Document({
  creator: "Juan Felipe Bernal", title: "Guía de anotación de ofertas de empleo",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: AZUL }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: "Arial", color: NARANJA }, paragraph: { spacing: { before: 220, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ...["reglas", "lista"].map((ref) => ({ reference: ref, levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] })),
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Guía de anotación · ", color: GRIS, size: 18 }), new TextRun({ children: [PageNumber.CURRENT], color: GRIS, size: 18 })] })] }) },
    children: contenido,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(process.argv[2], buf); console.log("escrito", process.argv[2], buf.length, "bytes"); });
