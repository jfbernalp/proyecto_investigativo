import time
from abc import ABC, abstractmethod
import pandas as pd
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Sequence

# Esperas ante 429 / 5xx. LinkedIn responde 429 de forma intermitente y sin Retry-After.
ESPERAS_REINTENTO_SEG = (10, 30, 60)
CODIGOS_REINTENTABLES = {429, 500, 502, 503, 504}


class BaseScraper(ABC):
    """
    Clase abstracta base que define la interfaz común para todos los scrapers de portales.
    """

    def __init__(self, portal_name: str, headers: Optional[Dict[str, str]] = None, timeout: int = 15):
        self.portal_name = portal_name
        self.headers = headers or {}
        self.timeout = timeout
        self.data: List[Dict[str, Any]] = []

    @abstractmethod
    def scrape(self, role: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Método obligatorio para ejecutar el scraping de ofertas para un rol específico.
        """
        pass

    def _get_con_reintentos(
        self,
        session: requests.Session,
        url: str,
        esperas: Sequence[int] = ESPERAS_REINTENTO_SEG,
    ) -> Optional[requests.Response]:
        """
        GET que reintenta ante límites de tasa o errores transitorios, respetando Retry-After si
        viene. Devuelve la respuesta final (aunque no sea 200) o None si falló la red.
        """
        for intento in range(len(esperas) + 1):
            try:
                respuesta = session.get(url, headers=self.headers, timeout=self.timeout)
            except requests.exceptions.RequestException as e:
                print(f"[{self.portal_name}] [RED] {e}")
                respuesta = None
            if respuesta is not None and respuesta.status_code not in CODIGOS_REINTENTABLES:
                return respuesta
            if intento == len(esperas):
                return respuesta
            retry_after = respuesta.headers.get("Retry-After") if respuesta is not None else None
            espera = int(retry_after) if retry_after and retry_after.isdigit() else esperas[intento]
            codigo = respuesta.status_code if respuesta is not None else "red"
            print(f"[{self.portal_name}] [{codigo}] reintento {intento + 1}/{len(esperas)} en {espera}s")
            time.sleep(espera)
        return None

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convierte los registros extraídos en un DataFrame de pandas.
        """
        return pd.DataFrame(self.data)

    def save_to_excel(self, file_path: Path) -> None:
        """
        Exporta los datos recolectados a formato Excel de forma segura.
        """
        from src.processing.cleaner import sanitizar_dataframe_para_excel
        df = sanitizar_dataframe_para_excel(self.to_dataframe())
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(file_path, index=False)
        print(f"[{self.portal_name.upper()}] Datos guardados exitosamente en: {file_path}")
