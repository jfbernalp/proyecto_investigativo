# Revisión crítica del informe de Scopus AI (7-nov-2026)

Archivo: `docs/articulo/Scopus - Scopus AI.pdf`. Informe de 14 páginas generado por Scopus AI con el tema
*Integrating Web Scraping, Relational Databases, and Large Language Models for Labor Market Analytics
and Curriculum Design*. Sus 66 referencias son las mismas de `scopus.bib`: 65 de 66 coinciden por título.
**No aporta fuentes nuevas.**

## Qué sirve

- **Diagnóstico general coherente con nuestro aporte:** los componentes por separado (scraping,
  limpieza, LLM para currículo) están estudiados, pero **faltan sistemas integrados de punta a punta y una
  evaluación estandarizada**. Coincide con la revisión sistemática #44 (validación limitada, datasets no
  estandarizados) y es el hueco que ocupa el Artículo 1.
- **Temas recurrentes:** supervisión humana, sesgo y alucinación, privacidad y anonimización (#43).
- **Agenda futura:** *pipelines* integrados con benchmarks, evaluación multinivel, marcos éticos para
  América Latina. Sirve para la sección de trabajo futuro, formulada con nuestras propias palabras y
  fuentes.

## Afirmaciones que NO deben citarse tal cual

El informe es una síntesis generada por IA. Varias afirmaciones atribuyen a las fuentes más de lo que
dicen sus resúmenes:

| Afirmación del informe | Fuentes que cita | Problema |
|---|---|---|
| «Selenium sobresale para portales de empleo» | Prueba automatizada con Selenium; comparación de librerías | Ninguna estudia portales de empleo. Generalización. |
| «América Latina enfatiza equidad y transparencia, pero carece de leyes específicas de IA» | Liu (2026, ley del Reino Unido sobre discriminación por sexo); Posada (2026, trabajo de datos en Venezuela) | **Ninguna analiza el marco legal latinoamericano.** Afirmación sin respaldo. |
| «Transformers visión-lenguaje y RL mejoran la extracción en sitios de empleo multilingües» | PeRL (razonamiento visión-lenguaje); dataset Bletchley | No tratan sitios de empleo. Relevancia inventada. |
| «Arquitecturas híbridas para analítica en tiempo real» en *pipelines* laborales | SnappyData (2016) | Sistema genérico de bases de datos, ajeno al dominio. |
| Destilación con «currículo» como optimización para diseño curricular | Difficulty-Aware Curriculum… (2027) | Falso amigo: *curriculum learning* de aprendizaje automático, no currículo educativo. |
| «Los pipelines de limpieza con LLM son esenciales para integrar con PostgreSQL» | Mehra & Rezig (2024); Akbiyik et al. (2025) | Ninguna trata PostgreSQL ni datos laborales. «PostgreSQL» viene del tema que se le dio al buscador. |
| «BERT: comprensión semántica superior, alto recall» | Nkrumah et al. (2025, WIP) | Un solo estudio preliminar con datos sintéticos (ver #61); no es un resultado general. |

## Decisiones para el artículo

1. **No citar el informe de Scopus AI como fuente.** Usarlo solo como mapa; cada afirmación se respalda
   con el artículo original leído.
2. **Declarar en la metodología** el uso de herramientas de IA en la búsqueda bibliográfica, si la
   revista lo exige.
3. **No adoptar su recomendación de limpieza con LLM sin discutirla:** nuestra elección de reglas
   explícitas se justifica por auditabilidad y reproducibilidad, y #30 encontró que el LLM sin contexto
   (*zero-shot*) rinde peor que el NLP tradicional. La línea base LLM del plan de evaluación lo pone a
   prueba.
4. **Observación útil para la motivación:** el propio informe muestra el problema que aborda nuestro
   verificador. Un LLM produce texto fluido con atribuciones a fuentes que no las respaldan. Puede
   mencionarse como ejemplo ilustrativo, con cuidado de no generalizar.
5. **Sigue sin cubrir** lo que falta en la biblioteca: Design Science Research, economía de los avisos
   en línea, precio de las habilidades, benchmarks de extracción, alucinación y verificación, legalidad
   del scraping y literatura de Colombia y América Latina (ver `consultas_scopus.md`).
