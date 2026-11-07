# Consultas de Scopus para cubrir los vacíos del Artículo 1

Preparadas el 7-nov-2026. Usar en **Scopus → Advanced document search**; pegar cada consulta tal cual.

**Cómo exportar cada búsqueda:**
1. Ordenar por **Cited by (highest)**.
2. Si hay más de unos 150 resultados, exportar los 50 más citados y, aparte, los de 2024–2026 (lo reciente
   todavía no acumula citas).
3. **Export → BibTeX**, marcando *Citation information*, *Bibliographical information* y
   **Abstract & keywords**.
4. Guardar en esta carpeta con el nombre indicado en cada consulta.

Registrar en la tabla del final la fecha y el número de resultados de cada búsqueda: el artículo debe
describir el protocolo de búsqueda.

---

## Parte 1: referencias puntuales (clásicos que un revisor espera)

Son títulos que conozco; **la búsqueda confirma autores, año y DOI antes de citarlos**. Exportar todos
juntos como `q0_clasicos.bib`.

```
TITLE("design science in information systems research")
OR TITLE("a design science research methodology for information systems research")
OR TITLE("skill requirements across firms and labor markets")
OR TITLE("do recessions accelerate routine-biased technological change")
OR TITLE("what is the price of a skill")
OR TITLE("SkillSpan")
OR TITLE("survey of hallucination in natural language generation")
OR TITLE("FActScore")
OR TITLE("retrieval-augmented generation for knowledge-intensive NLP tasks")
OR TITLE("legality and ethics of web scraping")
OR TITLE("controlling the false discovery rate")
OR TITLE("some heteroskedasticity-consistent covariance matrix estimators")
```

Si alguno no aparece (por ejemplo, porque la revisión sobre extracción de habilidades de Senger et al.,
2024, salió en un taller de ACL), buscarlo en Google Scholar o en la ACL Anthology y anotarlo aparte.

---

## Parte 2: búsquedas temáticas

### Q1 · Design Science Research aplicada a sistemas con IA generativa → `q1_dsr_ia.bib`
```
TITLE-ABS-KEY("design science") AND TITLE-ABS-KEY("large language model*" OR "generative AI" OR "generative artificial intelligence") AND PUBYEAR > 2021
```

### Q2 · Representatividad y validación de avisos de empleo en línea → `q2_representatividad.bib`
```
TITLE-ABS-KEY("online job ad*" OR "online job advert*" OR "online job posting*" OR "job vacanc* data" OR "vacancy data") AND TITLE-ABS-KEY(representativ* OR bias OR coverage OR validat*)
```

### Q3 · Primas salariales por habilidad desde avisos → `q3_primas.bib`
```
TITLE-ABS-KEY("job posting*" OR "job ad*" OR "job advert*" OR vacanc*) AND TITLE-ABS-KEY("skill premium*" OR "wage premium*" OR "skill price*" OR "returns to skill*" OR "posted wage*")
```

### Q4 · Extracción de habilidades: conjuntos etiquetados y evaluación → `q4_extraccion.bib`
```
TITLE-ABS-KEY("skill extraction" OR "skill identification" OR "skill recognition" OR "skill mining") AND TITLE-ABS-KEY("job posting*" OR "job ad*" OR "job description*" OR vacanc*) AND TITLE-ABS-KEY(annotat* OR benchmark OR dataset OR "gold standard" OR evaluat*)
```

### Q5 · Alucinaciones numéricas y verificación de cifras en LLM → `q5_verificacion.bib`
El nicho exacto de nuestro verificador: cifras inventadas o mal atribuidas.
```
TITLE-ABS-KEY(hallucinat* OR "factual consistency" OR "fact verification" OR "fact-checking" OR grounded* OR faithfulness) AND TITLE-ABS-KEY("large language model*" OR LLM*) AND TITLE-ABS-KEY(numer* OR quantitative OR statistic* OR "numerical claim*" OR table*) AND PUBYEAR > 2022
```

### Q6 · LLM para diseño curricular con supervisión humana → `q6_curriculo_humano.bib`
```
TITLE-ABS-KEY("large language model*" OR "generative AI" OR ChatGPT OR GPT*) AND TITLE-ABS-KEY(curricul* OR "program design" OR "course design" OR "syllabus") AND TITLE-ABS-KEY("human-in-the-loop" OR "human oversight" OR "expert review" OR "expert evaluation" OR "teacher review")
```

### Q7 · Ética y legalidad del web scraping → `q7_etica_scraping.bib`
```
TITLE-ABS-KEY("web scraping" OR "web crawling" OR "data scraping") AND TITLE-ABS-KEY(ethic* OR legal* OR "terms of service" OR "terms of use" OR copyright OR "data protection" OR privacy)
```

### Q8 · Mercado laboral y avisos en Colombia y América Latina → `q8_latam.bib`
```
TITLE-ABS-KEY("labor market" OR "labour market" OR "mercado laboral" OR "mercado de trabajo" OR employment OR empleo) AND TITLE-ABS-KEY(observator* OR "job posting*" OR "job ad*" OR vacant* OR "ofertas de empleo" OR vacantes) AND (TITLE-ABS-KEY(Colombia OR "Latin America" OR "América Latina" OR Mexico OR Chile OR Peru OR Argentina OR Brazil) OR AFFILCOUNTRY(Colombia))
```

### Q9 · Demanda de habilidades en roles de datos → `q9_roles_datos.bib`
```
TITLE-ABS-KEY("data scientist*" OR "data science" OR "data analyst*" OR "data engineer*" OR "business intelligence") AND TITLE-ABS-KEY("job posting*" OR "job ad*" OR "job market" OR "labor market" OR "labour market") AND TITLE-ABS-KEY(skill* OR competenc*)
```

---

## Registro de búsquedas (completar al ejecutar)

| Consulta | Fecha | Resultados | Exportados | Archivo |
|---|---|------------|---|---|
| Q0 clásicos | 7-nov-2026 | 3          | 8 (archivo q0_scholar.bib) + 9 completados en Crossref/DataCite | q0_clasicos.bib |
| Q1 | 7-nov-2026 | 369        | 100 | q1_dsr_ia.bib |
| Q2 | 7-nov-2026 | 53         | 53 | q2_representatividad.bib |
| Q3 | 7-nov-2026 | 47         | 47 | q3_primas.bib |
| Q4 | 7-nov-2026 | 53         | 53 | q4_extraccion.bib |
| Q5 | 7-nov-2026 | 2252       | 100 | q5_verificacion.bib |
| Q6 | 7-nov-2026 | 206        | 200 | q6_curriculo_humano.bib |
| Q7 | 7-nov-2026 | 441        | 200 | q7_etica_scraping.bib |
| Q8 | 7-nov-2026 | 52         | 52 | q8_latam.bib |
| Q9 | 7-nov-2026 | 214        | 214 | q9_roles_datos.bib |
