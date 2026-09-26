import os
import hashlib
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from typing import Optional, List, Dict, Any

# Configuración de base de datos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "labor_market.db"

# Cargar .env automáticamente si existe
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

class DatabaseManager:
    """
    Gestor centralizado de Base de Datos relacional para el proyecto con soporte de
    Snapshots Históricos (Time-Series) y Modelo Dimensional (Esquema Estrella).
    Soporta SQLite local y bases de datos en la nube (PostgreSQL / MySQL / Supabase).
    """

    def __init__(self, connection_url: Optional[str] = None):
        self.connection_url = connection_url or DATABASE_URL
        if self.connection_url.startswith("postgres://"):
            self.connection_url = self.connection_url.replace("postgres://", "postgresql://", 1)
        
        try:
            self.engine = create_engine(self.connection_url, echo=False)
            # Probar conexión temprana
            with self.engine.connect() as test_conn:
                pass
            print(f"[DATABASE] Conectado a: {self._get_safe_connection_name()}")
        except Exception as e_conn:
            print(f"[DATABASE AVISO] No fue posible conectar a la BD remota ({e_conn}). Usando SQLite local.")
            self.connection_url = f"sqlite:///{DEFAULT_DB_PATH}"
            self.engine = create_engine(self.connection_url, echo=False)
            print(f"[DATABASE] Conectado a: {self._get_safe_connection_name()}")

        self.crear_tablas_dimensionales()

    def _get_safe_connection_name(self) -> str:
        if "sqlite" in self.connection_url:
            return f"SQLite ({DEFAULT_DB_PATH.name})"
        return self.connection_url.split("@")[-1] if "@" in self.connection_url else "Cloud Database"

    def crear_tablas_dimensionales(self) -> None:
        """
        Crea las tablas del modelo estrella dimensional para series de tiempo si no existen.
        """
        queries = [
            # 1. Dimensión Ofertas (Metadata inmutable de vacantes)
            """
            CREATE TABLE IF NOT EXISTS dim_ofertas (
                id_vacante_hash VARCHAR(64) PRIMARY KEY,
                portal VARCHAR(100),
                rol_buscado VARCHAR(150),
                nombre_oferta TEXT,
                empresa TEXT,
                ubicacion TEXT,
                modalidad VARCHAR(100),
                seniority VARCHAR(100),
                tipo_mercado VARCHAR(150),
                moneda_original VARCHAR(50),
                url TEXT,
                primera_fecha_deteccion DATE,
                ultima_fecha_deteccion DATE
            );
            """,
            # 2. Hechos de Extracción Histórica (Snapshots por corrida mensual)
            """
            CREATE TABLE IF NOT EXISTS fact_extracciones_historico (
                id_extraccion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_vacante_hash VARCHAR(64),
                fecha_extraccion DATE,
                mes_periodo INTEGER,
                salario_original TEXT,
                salario_cop_mensual FLOAT,
                salario_millones FLOAT,
                anios_experiencia FLOAT,
                nivel_educativo_ordinal FLOAT,
                total_habilidades_detectadas INTEGER
            );
            """,
            # 3. Hechos de Habilidades Históricas (Desagregación 1 a N por mes)
            """
            CREATE TABLE IF NOT EXISTS fact_habilidades_historico (
                id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
                id_vacante_hash VARCHAR(64),
                habilidad TEXT,
                fecha_extraccion DATE,
                mes_periodo INTEGER,
                portal VARCHAR(100),
                tipo_mercado VARCHAR(150),
                salario_cop_mensual FLOAT
            );
            """,
            # 4. Agregaciones Métricas Mensuales (KPIs consolidados para series de tiempo)
            """
            CREATE TABLE IF NOT EXISTS agg_metricas_mensuales (
                mes_periodo INTEGER,
                habilidad VARCHAR(255),
                tipo_mercado VARCHAR(150),
                total_ofertas_demandadas INTEGER,
                porcentaje_demanda FLOAT,
                salario_promedio_cop FLOAT,
                salario_mediana_cop FLOAT,
                PRIMARY KEY (mes_periodo, habilidad, tipo_mercado)
            );
            """,
            # 5. Diagnóstico Ejecutivo FODA e Índice de Competitividad Curricular IA
            """
            CREATE TABLE IF NOT EXISTS fact_diagnostico_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                programa_evaluado VARCHAR(200),
                puntuacion_competitividad NUMERIC(5,2),
                resumen_ejecutivo TEXT,
                fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 6. Dimensión Propuestas Curriculares MIG
            """
            CREATE TABLE IF NOT EXISTS dim_propuestas_curriculares_mig (
                id_propuesta VARCHAR(64) PRIMARY KEY,
                tipo_propuesta VARCHAR(100),
                nombre_programa VARCHAR(250),
                titulo_otorgado VARCHAR(250),
                nivel_academico VARCHAR(100),
                duracion_estimada VARCHAR(100),
                creditos_totales INTEGER,
                horas_totales INTEGER,
                modalidad VARCHAR(100),
                horario TEXT,
                fecha_inicio_estimada VARCHAR(100),
                fecha_terminacion_estimada VARCHAR(100),
                proximas_ediciones VARCHAR(150),
                inversion_publico_externo TEXT,
                inversion_comunidad_unicafam TEXT,
                inversion_egresados TEXT,
                inversion_grupos TEXT,
                justificacion_detallada TEXT,
                objetivos_programa TEXT,
                dirigido_a TEXT,
                metodologia_detallada TEXT,
                valores_agregados TEXT,
                perfil_ingreso TEXT,
                perfil_egreso TEXT,
                roles_objetivo TEXT,
                impacto_salarial_proyectado TEXT,
                url_descarga_excel TEXT
            );
            """,
            # 7. Hechos Módulos y Malla MIG
            """
            CREATE TABLE IF NOT EXISTS fact_modulos_propuestas_mig (
                id_modulo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_propuesta VARCHAR(64),
                numero_modulo INTEGER,
                nombre_modulo VARCHAR(250),
                semestre_sugerido VARCHAR(50),
                creditos INTEGER,
                horas_tfd INTEGER,
                horas_tti INTEGER,
                horas_totales_modulo INTEGER,
                contenido_detallado TEXT,
                cronograma_fechas TEXT,
                stack_tecnologico TEXT,
                raes TEXT,
                justificacion_mercado TEXT
            );
            """,
            # 8. Dimensión Docentes MIG
            """
            CREATE TABLE IF NOT EXISTS dim_docentes_propuestas_mig (
                id_docente INTEGER PRIMARY KEY AUTOINCREMENT,
                id_propuesta VARCHAR(64),
                nombre_o_rol VARCHAR(250),
                modulo_asignado VARCHAR(250),
                perfil_experto TEXT
            );
            """
        ]

        with self.engine.begin() as conn:
            for q in queries:
                # Ajuste de AUTOINCREMENT según SQLite o PostgreSQL
                if "postgresql" in self.connection_url:
                    q = q.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                conn.execute(text(q))

            # Crear Vistas Optimizadas para Superset
            vistas = [
                """
                CREATE VIEW IF NOT EXISTS view_superset_oferta_academica_mig AS
                SELECT 
                    p.id_propuesta,
                    p.tipo_propuesta,
                    p.nombre_programa,
                    p.titulo_otorgado,
                    p.nivel_academico,
                    p.modalidad,
                    p.duracion_estimada,
                    p.creditos_totales,
                    p.horas_totales,
                    p.horario,
                    p.fecha_inicio_estimada,
                    p.proximas_ediciones,
                    p.inversion_publico_externo,
                    p.inversion_comunidad_unicafam,
                    p.inversion_egresados,
                    p.inversion_grupos,
                    p.impacto_salarial_proyectado,
                    p.roles_objetivo,
                    p.justificacion_detallada,
                    p.objetivos_programa,
                    p.metodologia_detallada,
                    p.valores_agregados,
                    COUNT(m.id_modulo) AS total_modulos,
                    p.url_descarga_excel,
                    ('<a href="' || COALESCE(p.url_descarga_excel, '#') || '" target="_blank" style="background-color: #1F4E79; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block;">📥 Descargar MIG (.xlsx)</a>') AS boton_descarga_html
                FROM dim_propuestas_curriculares_mig p
                LEFT JOIN fact_modulos_propuestas_mig m ON p.id_propuesta = m.id_propuesta
                GROUP BY 
                    p.id_propuesta, p.tipo_propuesta, p.nombre_programa, p.titulo_otorgado, p.nivel_academico,
                    p.modalidad, p.duracion_estimada, p.creditos_totales, p.horas_totales, p.horario,
                    p.fecha_inicio_estimada, p.proximas_ediciones, p.inversion_publico_externo,
                    p.inversion_comunidad_unicafam, p.inversion_egresados, p.inversion_grupos,
                    p.impacto_salarial_proyectado, p.roles_objetivo, p.justificacion_detallada,
                    p.objetivos_programa, p.metodologia_detallada, p.valores_agregados, p.url_descarga_excel;
                """,
                """
                CREATE VIEW IF NOT EXISTS view_superset_malla_curricular_mig AS
                SELECT 
                    m.id_modulo,
                    p.id_propuesta,
                    p.nombre_programa,
                    p.tipo_propuesta,
                    p.nivel_academico,
                    m.numero_modulo,
                    m.nombre_modulo,
                    m.creditos,
                    m.horas_tfd,
                    m.horas_tti,
                    m.horas_totales_modulo,
                    m.cronograma_fechas,
                    m.stack_tecnologico,
                    m.raes,
                    m.justificacion_mercado,
                    d.nombre_o_rol AS docente_asignado,
                    d.perfil_experto AS perfil_docente_experto
                FROM fact_modulos_propuestas_mig m
                JOIN dim_propuestas_curriculares_mig p ON m.id_propuesta = p.id_propuesta
                LEFT JOIN dim_docentes_propuestas_mig d ON m.id_propuesta = d.id_propuesta AND m.nombre_modulo = d.modulo_asignado;
                """,
                """
                CREATE VIEW IF NOT EXISTS view_superset_kpis_curriculares_mig AS
                SELECT 
                    d.id,
                    d.programa_evaluado,
                    d.puntuacion_competitividad AS indice_competitividad_mercado,
                    (SELECT COUNT(*) FROM dim_propuestas_curriculares_mig) AS total_propuestas_generadas,
                    (SELECT SUM(creditos_totales) FROM dim_propuestas_curriculares_mig) AS total_creditos_ofertados,
                    (SELECT SUM(horas_totales) FROM dim_propuestas_curriculares_mig) AS total_horas_formacion,
                    (SELECT COUNT(*) FROM fact_modulos_propuestas_mig) AS total_modulos_disenados,
                    d.resumen_ejecutivo,
                    d.fecha_generacion
                FROM fact_diagnostico_ia d
                ORDER BY d.fecha_generacion DESC
                LIMIT 1;
                """
            ]
            for v in vistas:
                if "postgresql" in self.connection_url:
                    v = v.replace("CREATE VIEW IF NOT EXISTS", "CREATE OR REPLACE VIEW")
                try:
                    conn.execute(text(v))
                except Exception as e_view:
                    print(f"[DATABASE AVISO] Vista Superset omitida o ya existente: {e_view}")

        # Migración automática / Ensanchamiento de columnas en PostgreSQL
        if "postgresql" in self.connection_url:
            alter_queries = [
                "ALTER TABLE fact_habilidades_historico ALTER COLUMN habilidad TYPE TEXT;",
                "ALTER TABLE dim_ofertas ALTER COLUMN nombre_oferta TYPE TEXT;",
                "ALTER TABLE dim_ofertas ALTER COLUMN empresa TYPE TEXT;",
                "ALTER TABLE dim_ofertas ALTER COLUMN ubicacion TYPE TEXT;",
                "ALTER TABLE fact_extracciones_historico ALTER COLUMN salario_original TYPE TEXT;"
            ]
            with self.engine.begin() as conn:
                for aq in alter_queries:
                    try:
                        conn.execute(text(aq))
                    except Exception:
                        pass

    @staticmethod
    def generar_hash_vacante(portal: str, codigo: str) -> str:
        """
        Genera un identificador único determinista SHA256 para cada vacante.
        """
        raw_key = f"{str(portal).strip()}_{str(codigo).strip()}".lower()
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    def registrar_snapshot_historico(self, df_modelado: pd.DataFrame, df_largo: pd.DataFrame) -> None:
        """
        Persiste los datos de la corrida actual en el modelo dimensional histórico
        asignando la fecha de extracción y el período de tiempo YYYYMM.
        """
        if df_modelado.empty:
            print("[DATABASE] DataFrame vacío, no se registró snapshot.")
            return

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        mes_periodo = int(datetime.now().strftime("%Y%m"))

        df_m = df_modelado.copy()
        
        # Generar hash único
        df_m["id_vacante_hash"] = df_m.apply(
            lambda r: self.generar_hash_vacante(r.get("Portal", "N/A"), r.get("Codigo", "N/A")), 
            axis=1
        )
        df_m["fecha_extraccion"] = fecha_hoy
        df_m["mes_periodo"] = mes_periodo

        # 1. Actualizar dim_ofertas (Upsert / Inserción de nuevas vacantes)
        dim_cols = {
            "id_vacante_hash": "id_vacante_hash",
            "Portal": "portal",
            "Rol_Buscado": "rol_buscado",
            "Nombre Oferta": "nombre_oferta",
            "Empresa": "empresa",
            "Ubicacion": "ubicacion",
            "Modalidad": "modalidad",
            "Seniority": "seniority",
            "Tipo_Mercado": "tipo_mercado",
            "Moneda_Original": "moneda_original",
            "URL": "url"
        }
        df_dim = df_m[[c for c in dim_cols.keys() if c in df_m.columns]].copy()
        df_dim = df_dim.rename(columns=dim_cols)
        
        # Clasificación automática de rol basada en el título de la oferta
        try:
            from src.processing.cleaner import clasificar_rol_tecnico
            df_dim["rol_buscado"] = df_dim["nombre_oferta"].apply(clasificar_rol_tecnico)
        except Exception:
            pass

        df_dim["primera_fecha_deteccion"] = fecha_hoy
        df_dim["ultima_fecha_deteccion"] = fecha_hoy

        # Guardar / Actualizar dimensión
        with self.engine.begin() as conn:
            for _, row in df_dim.iterrows():
                # En SQLite usamos INSERT OR REPLACE / En PostgreSQL ON CONFLICT DO UPDATE
                if "sqlite" in self.connection_url:
                    stmt = text("""
                        INSERT INTO dim_ofertas (
                            id_vacante_hash, portal, rol_buscado, nombre_oferta, empresa,
                            ubicacion, modalidad, seniority, tipo_mercado, moneda_original,
                            url, primera_fecha_deteccion, ultima_fecha_deteccion
                        ) VALUES (
                            :id_vacante_hash, :portal, :rol_buscado, :nombre_oferta, :empresa,
                            :ubicacion, :modalidad, :seniority, :tipo_mercado, :moneda_original,
                            :url, :primera_fecha_deteccion, :ultima_fecha_deteccion
                        )
                        ON CONFLICT(id_vacante_hash) DO UPDATE SET
                            ultima_fecha_deteccion = :ultima_fecha_deteccion,
                            modalidad = :modalidad,
                            seniority = :seniority;
                    """)
                else:
                    stmt = text("""
                        INSERT INTO dim_ofertas (
                            id_vacante_hash, portal, rol_buscado, nombre_oferta, empresa,
                            ubicacion, modalidad, seniority, tipo_mercado, moneda_original,
                            url, primera_fecha_deteccion, ultima_fecha_deteccion
                        ) VALUES (
                            :id_vacante_hash, :portal, :rol_buscado, :nombre_oferta, :empresa,
                            :ubicacion, :modalidad, :seniority, :tipo_mercado, :moneda_original,
                            :url, :primera_fecha_deteccion, :ultima_fecha_deteccion
                        )
                        ON CONFLICT (id_vacante_hash) DO UPDATE SET
                            ultima_fecha_deteccion = EXCLUDED.ultima_fecha_deteccion,
                            modalidad = EXCLUDED.modalidad,
                            seniority = EXCLUDED.seniority;
                    """)
                conn.execute(stmt, row.to_dict())

        # 2. Registrar en fact_extracciones_historico
        fact_cols = {
            "id_vacante_hash": "id_vacante_hash",
            "fecha_extraccion": "fecha_extraccion",
            "mes_periodo": "mes_periodo",
            "Salario": "salario_original",
            "Salario_COP": "salario_cop_mensual",
            "Salario_Millones": "salario_millones",
            "Anios_Experiencia": "anios_experiencia",
            "Nivel_Educativo_Ordinal": "nivel_educativo_ordinal",
            "Total_Habilidades_Detectadas": "total_habilidades_detectadas"
        }
        df_fact = df_m[[c for c in fact_cols.keys() if c in df_m.columns]].copy()
        df_fact = df_fact.rename(columns=fact_cols)
        df_fact.to_sql("fact_extracciones_historico", con=self.engine, if_exists="append", index=False)

        # 3. Registrar en fact_habilidades_historico
        if not df_largo.empty:
            df_l = df_largo.copy()
            df_l["id_vacante_hash"] = df_l.apply(
                lambda r: self.generar_hash_vacante(r.get("Portal", "N/A"), r.get("Codigo", "N/A")), 
                axis=1
            )
            df_l["fecha_extraccion"] = fecha_hoy
            df_l["mes_periodo"] = mes_periodo

            largo_cols = {
                "id_vacante_hash": "id_vacante_hash",
                "Habilidad": "habilidad",
                "fecha_extraccion": "fecha_extraccion",
                "mes_periodo": "mes_periodo",
                "Portal": "portal",
                "Tipo_Mercado": "tipo_mercado",
                "Salario_COP": "salario_cop_mensual"
            }
            df_l_fact = df_l[[c for c in largo_cols.keys() if c in df_l.columns]].copy()
            df_l_fact = df_l_fact.rename(columns=largo_cols)
            df_l_fact.to_sql("fact_habilidades_historico", con=self.engine, if_exists="append", index=False)

        # 4. Calcular y actualizar agg_metricas_mensuales
        self._recalcular_metricas_mensuales(mes_periodo)

        # 5. Sincronizar tablas de BI para compatibilidad con el Dashboard
        self.guardar_dataframe(df_m, table_name="ofertas_modeladas_bi", if_exists="replace")
        if not df_largo.empty:
            self.guardar_dataframe(df_largo, table_name="habilidades_desagregadas_bi", if_exists="replace")

        print(f"[DATABASE HISTÓRICO] Snapshot de {fecha_hoy} (Período {mes_periodo}) persistido exitosamente en el Modelo Dimensional.")

    def _recalcular_metricas_mensuales(self, mes_periodo: int) -> None:
        """
        Recalcula los KPIs agregados por habilidad y mercado para el período actual.
        """
        try:
            round_expr = "ROUND(AVG(h.salario_cop_mensual)::numeric, 2)" if "postgresql" in self.connection_url else "ROUND(AVG(h.salario_cop_mensual), 2)"
            query = f"""
            SELECT 
                h.mes_periodo,
                h.habilidad,
                h.tipo_mercado,
                COUNT(*) as total_ofertas_demandadas,
                {round_expr} as salario_promedio_cop
            FROM fact_habilidades_historico h
            WHERE h.mes_periodo = {mes_periodo}
            GROUP BY h.mes_periodo, h.habilidad, h.tipo_mercado;
            """
            df_agg = pd.read_sql_query(query, con=self.engine)
            if not df_agg.empty:
                # Calcular total ofertas del período para porcentaje
                totales = pd.read_sql_query(
                    f"SELECT tipo_mercado, COUNT(*) as total_mes FROM fact_extracciones_historico e JOIN dim_ofertas d ON e.id_vacante_hash = d.id_vacante_hash WHERE e.mes_periodo = {mes_periodo} GROUP BY tipo_mercado", 
                    con=self.engine
                ).set_index("tipo_mercado")["total_mes"].to_dict()

                df_agg["porcentaje_demanda"] = df_agg.apply(
                    lambda r: round((r["total_ofertas_demandadas"] / totales.get(r["tipo_mercado"], 1)) * 100, 2), 
                    axis=1
                )
                df_agg["salario_mediana_cop"] = df_agg["salario_promedio_cop"] # Proxy

                # Guardar agregación mensual
                df_agg.to_sql("agg_metricas_mensuales", con=self.engine, if_exists="replace", index=False)
        except Exception as e:
            print(f"[DATABASE AVISO] Error al recalcular métricas mensuales: {e}")

    def guardar_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
        """
        Persiste un DataFrame como tabla relacional.
        """
        try:
            df_to_save = df.copy()
            # Renombrar columnas con caracteres conflictivos en SQL como '%'
            df_to_save.columns = [str(c).replace("%", "Pct") for c in df_to_save.columns]

            for col in df_to_save.columns:
                if df_to_save[col].apply(lambda x: isinstance(x, (list, dict))).any():
                    df_to_save[col] = df_to_save[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x) if pd.notna(x) else "")
                elif df_to_save[col].dtype == object:
                    # Convertir posibles tipos numpy a tipos estándar
                    df_to_save[col] = df_to_save[col].apply(lambda x: float(x) if hasattr(x, 'item') and isinstance(x.item(), float) else str(x) if pd.notna(x) and not isinstance(x, (int, float, str, bool)) else x)

            df_to_save.to_sql(table_name, con=self.engine, if_exists=if_exists, index=False)
            print(f"[DATABASE] Tabla '{table_name}' actualizada con {len(df_to_save)} registros.")
        except Exception as e:
            print(f"[DATABASE ERROR] Error guardando tabla '{table_name}': {e}")

    def leer_tabla(self, table_name: str) -> pd.DataFrame:
        """
        Lee una tabla relacional completa.
        """
        try:
            query = f"SELECT * FROM {table_name}"
            return pd.read_sql_query(query, con=self.engine)
        except Exception as e:
            print(f"[DATABASE ERROR] Error leyendo tabla '{table_name}': {e}")
            return pd.DataFrame()

    def ejecutar_consulta(self, sql_query: str) -> pd.DataFrame:
        """
        Ejecuta una consulta SQL personalizada.
        """
        try:
            return pd.read_sql_query(sql_query, con=self.engine)
        except Exception as e:
            print(f"[DATABASE ERROR] Error ejecutando consulta SQL: {e}")
            return pd.DataFrame()

    def listar_tablas(self) -> List[str]:
        """
        Retorna la lista de tablas existentes.
        """
        inspector = inspect(self.engine)
        return inspector.get_table_names()
