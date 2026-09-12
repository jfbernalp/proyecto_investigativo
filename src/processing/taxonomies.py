"""
Taxonomía de Habilidades Técnicas y Competencias en Ciencia y Analítica de Datos.
"""

TAXONOMIA_HABILIDADES = {
    # Lenguajes de Programación y Consulta
    "Python": r"\bpython\b",
    "R": r"\b[rR]\b(?:\s*studio|\s*language|\s*lenguaje)?",
    "SQL": r"\bsql\b|\bpostgresql\b|\bmysql\b|\boracle\b|\bsql\s*server\b|\bpl/sql\b",
    "Scala": r"\bscala\b",
    "Java / C++": r"\bjava\b|\bc\+\+\b|\bc#\b",
    
    # Visualización y Business Intelligence (BI)
    "Power BI": r"\bpower\s*bi\b|\bpowerbi\b|\bdax\b",
    "Tableau": r"\btableau\b",
    "Excel Avanzado": r"\bexcel\b|\bhojas\s*de\s*c[aá]lculo\b|\bvba\b",
    "Looker": r"\blooker\b|\blooker\s*studio\b",
    "Qlik": r"\bqlik\b|\bqlikview\b|\bqliksense\b",

    # Big Data y Computación Distribuida
    "Spark / PySpark": r"\bspark\b|\bpyspark\b",
    "Databricks": r"\bdatabricks\b",
    "Hadoop / Hive": r"\bhadoop\b|\bhive\b",
    "Kafka": r"\bkafka\b",

    # Cloud Computing
    "AWS": r"\baws\b|\bamazon\s*web\s*services\b|\bredshift\b|\bs3\b|\bec2\b",
    "Azure": r"\bazure\b|\bsynapse\b|\bazure\s*ml\b",
    "Google Cloud (GCP)": r"\bgcp\b|\bgoogle\s*cloud\b|\bbigquery\b",

    # Machine Learning, IA y Estadística
    "Machine Learning General": r"\bmachine\s*learning\b|\baprendizaje\s*autom[aá]tico\b|\bml\b",
    "Deep Learning": r"\bdeep\s*learning\b|\baprendizaje\s*profundo\b|\bredes\s*neuronales\b",
    "NLP / LLMs": r"\bnlp\b|\bprocesamiento\s*de\s*lenguaje\s*natural\b|\bllm\b|\btransformers\b|\bbert\b|\bgpt\b",
    "Computer Vision": r"\bcomputer\s*vision\b|\bvisi[oó]n\s*por\s*computador[a]?\b|\bopencv\b",
    "Scikit-Learn": r"\bscikit-learn\b|\bsklearn\b",
    "TensorFlow / Keras": r"\btensorflow\b|\bkeras\b",
    "PyTorch": r"\bpytorch\b",
    "Estadística / Modelamiento": r"\bestad[ií]stic[ao]\b|\bmodelamiento\b|\bmodelado\s*predictivo\b|\bseries\s*de\s*tiempo\b",

    # Ingeniería de Datos & MLOps
    "ETL / Pipelines de Datos": r"\betl\b|\bpipelines?\b|\bflujos\s*de\s*datos\b|\bairbyte\b|\bdbt\b",
    "Airflow": r"\bairflow\b",
    "Docker / Kubernetes": r"\bdocker\b|\bkubernetes\b|\bcontenedores\b",
    "Git / Control de Versiones": r"\bgit\b|\bgithub\b|\bgitlab\b",
    "Bases de Datos NoSQL": r"\bnosql\b|\bmongodb\b|\bcassandra\b|\bredis\b|\belasticsearch\b",
    "MLOps": r"\bmlops\b|\bmlflow\b"
}

CLASIFICACION_CATEGORIAS = {
    "Lenguajes": ["Python", "R", "SQL", "Scala", "Java / C++"],
    "BI & Visualización": ["Power BI", "Tableau", "Excel Avanzado", "Looker", "Qlik"],
    "Big Data & Cloud": ["Spark / PySpark", "Databricks", "Hadoop / Hive", "Kafka", "AWS", "Azure", "Google Cloud (GCP)"],
    "Machine Learning & AI": ["Machine Learning General", "Deep Learning", "NLP / LLMs", "Computer Vision", "Scikit-Learn", "TensorFlow / Keras", "PyTorch", "Estadística / Modelamiento"],
    "Data Engineering & Ops": ["ETL / Pipelines de Datos", "Airflow", "Docker / Kubernetes", "Git / Control de Versiones", "Bases de Datos NoSQL", "MLOps"]
}
