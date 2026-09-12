from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

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
