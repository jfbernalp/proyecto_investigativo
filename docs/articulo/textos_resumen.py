TITULO_ES = ("Observatorio auditable del mercado laboral en datos con IA generativa anclada en evidencia: diseño y "
             "evaluación")
TITULO_EN = ("An auditable observatory of the data job market with evidence-grounded generative AI: design and "
             "evaluation")
RESUMEN = (
    "Las instituciones de educación superior necesitan ajustar sus programas en datos a un mercado laboral que cambia "
    "con rapidez, y los modelos de lenguaje propuestos para apoyar ese diseño curricular producen cifras sin respaldo. "
    "El objetivo fue diseñar y evaluar un observatorio auditable del mercado laboral en roles de datos que integra "
    "inteligencia artificial generativa anclada en evidencia, desarrollado para la actualización curricular de la "
    "Fundación Universitaria Cafam (UniCafam). Siguiendo la investigación en ciencia del diseño, se construyó un "
    "sistema que recolecta cada mes avisos de empleo de siete fuentes, extrae habilidades, rol y experiencia con "
    "reglas explícitas, estima la demanda y las primas salariales con intervalos de confianza, corrección por "
    "comparaciones múltiples y pruebas de equivalencia, y entrega a un modelo de lenguaje un contexto de mercado "
    "versionado como única fuente de cifras. Un verificador determinista revisa cada cifra generada y una persona "
    "aprueba cada propuesta. La evaluación, en tres rondas, usa 907 avisos únicos de septiembre a noviembre de 2026. "
    "En 36 generaciones controladas, con el contexto de mercado el verificador marcó entre 0 % y 0,7 % de las cifras "
    "revisadas; sin anclaje, entre 93,8 % y 100 %. Con 176 ofertas con salario, las primas de los roles de ingeniería "
    "y ciencia de datos frente al analista fueron concluyentes, mientras que ninguna prima por habilidad lo fue. La "
    "evaluación de la extracción frente a una referencia anotada a mano y de la precisión del verificador está en "
    "curso. Se concluye que anclar el modelo en un contexto versionado y verificar sus cifras con reglas reduce notablemente "
    "las cifras sin respaldo, y que declarar la ausencia de evidencia es una función central del "
    "observatorio. Las limitaciones principales son tres cortes mensuales, la representatividad de los avisos en "
    "línea y el tamaño de la muestra salarial.")
ABSTRACT = (
    "Higher education institutions need to align their data programs with a fast-changing labor market, and the "
    "language models proposed to support curriculum design produce unsupported figures. This study aimed to design and "
    "evaluate an auditable observatory of the labor market for data roles that integrates evidence-grounded generative "
    "artificial intelligence, developed for curriculum updating at Fundación Universitaria Cafam (UniCafam), Colombia. "
    "Following design science research, we built a system that collects job postings monthly from seven sources, "
    "extracts skills, role and experience with explicit rules, estimates demand and wage premiums with confidence "
    "intervals, multiple-comparison correction and equivalence tests, and provides a language model with a versioned "
    "market context as its only source of figures. A deterministic verifier checks every generated figure, and a "
    "person approves each proposal. The three-round evaluation uses 907 unique postings from September to November "
    "2026. In 36 controlled generations, with the market context the verifier flagged between 0% and 0.7% of the "
    "checked figures; without grounding, between 93.8% and 100%. With 176 postings reporting salary, the premiums of "
    "data engineering and data science roles over the analyst role were conclusive, while no skill premium was. The "
    "evaluation of extraction against a hand-annotated reference and of the verifier's precision is ongoing. We "
    "conclude that grounding the model in a versioned context and verifying its figures with rules markedly reduces "
    "unsupported figures, and that reporting the absence of evidence is a core function of the observatory. The main "
    "limitations are three monthly snapshots, the representativeness of online postings and the size of the salary "
    "sample.")
PALABRAS = ("mercado laboral, ciencia de datos, avisos de empleo, inteligencia artificial generativa, alucinación, "
            "verificación de datos, diseño curricular, investigación en ciencia del diseño.")
KEYWORDS = ("labor market, data science, job postings, generative artificial intelligence, hallucination, fact "
            "verification, curriculum design, design science research.")
AFILIACION = ("Estudiante de Ciencia de Datos, Fundación Universitaria Cafam (UniCafam), Facultad de Ingeniería, "
              "Semillero de Investigación Codex, ORCID https://orcid.org/0009-0005-2327-8974, Bogotá, Colombia, "
              "juan.bernal@unicafam.edu.co.")

if __name__ == "__main__":
    for n, t in (("título es", TITULO_ES), ("título en", TITULO_EN), ("resumen", RESUMEN), ("abstract", ABSTRACT)):
        print(n, len(t.split()))
