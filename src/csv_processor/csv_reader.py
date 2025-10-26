"""
Lector y procesador de archivos CSV con datos financieros
Detecta automáticamente el formato y extrae transacciones
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
import chardet
from datetime import datetime


class CSVReader:
    """Lee y procesa archivos CSV con datos financieros"""

    # Posibles nombres de columnas (en minúsculas)
    COLUMNAS_FECHA = ["fecha", "date", "fecha_transaccion", "transaction_date", "día", "dia"]
    COLUMNAS_MONTO = ["monto", "amount", "importe", "total", "valor", "precio"]
    COLUMNAS_DESCRIPCION = ["descripcion", "description", "concepto", "detalle", "detail"]
    COLUMNAS_CATEGORIA = ["categoria", "category", "tipo", "type", "rubro"]
    COLUMNAS_EMISOR = ["emisor", "receptor", "proveedor", "supplier", "vendedor", "cliente"]

    def __init__(self):
        """Inicializa el lector de CSV"""
        pass

    def detectar_encoding(self, ruta_archivo: str) -> str:
        """
        Detecta el encoding del archivo CSV

        Args:
            ruta_archivo: Ruta al archivo CSV

        Returns:
            Encoding detectado (utf-8, latin-1, etc.)
        """
        try:
            with open(ruta_archivo, 'rb') as f:
                resultado = chardet.detect(f.read())
                encoding = resultado['encoding']
                confianza = resultado['confidence']

                logger.debug(f"Encoding detectado: {encoding} (confianza: {confianza:.2%})")

                return encoding if encoding else 'utf-8'

        except Exception as e:
            logger.warning(f"Error al detectar encoding: {e}. Usando utf-8")
            return 'utf-8'

    def leer_csv(self, ruta_archivo: str) -> Optional[pd.DataFrame]:
        """
        Lee un archivo CSV y retorna un DataFrame

        Args:
            ruta_archivo: Ruta al archivo CSV

        Returns:
            DataFrame de pandas o None si hay error
        """
        try:
            # Detectar encoding
            encoding = self.detectar_encoding(ruta_archivo)

            # Intentar leer con diferentes delimitadores
            delimitadores = [',', ';', '\t', '|']

            for delim in delimitadores:
                try:
                    df = pd.read_csv(
                        ruta_archivo,
                        delimiter=delim,
                        encoding=encoding,
                        on_bad_lines='skip'
                    )

                    # Verificar que tenga columnas y filas
                    if len(df.columns) > 1 and len(df) > 0:
                        logger.info(f"✓ CSV leído: {len(df)} filas, {len(df.columns)} columnas (delim: '{delim}')")
                        return df

                except Exception:
                    continue

            logger.error(f"No se pudo leer el CSV con ningún delimitador")
            return None

        except Exception as e:
            logger.error(f"❌ Error al leer CSV {ruta_archivo}: {e}")
            return None

    def identificar_columnas(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Identifica las columnas importantes del DataFrame

        Args:
            df: DataFrame de pandas

        Returns:
            Diccionario mapeando tipo de dato -> nombre de columna
        """
        columnas_minusculas = {col.lower(): col for col in df.columns}

        mapeo = {}

        # Buscar columna de fecha
        for col_fecha in self.COLUMNAS_FECHA:
            if col_fecha in columnas_minusculas:
                mapeo['fecha'] = columnas_minusculas[col_fecha]
                break

        # Buscar columna de monto
        for col_monto in self.COLUMNAS_MONTO:
            if col_monto in columnas_minusculas:
                mapeo['monto'] = columnas_minusculas[col_monto]
                break

        # Buscar columna de descripción
        for col_desc in self.COLUMNAS_DESCRIPCION:
            if col_desc in columnas_minusculas:
                mapeo['descripcion'] = columnas_minusculas[col_desc]
                break

        # Buscar columna de categoría
        for col_cat in self.COLUMNAS_CATEGORIA:
            if col_cat in columnas_minusculas:
                mapeo['categoria'] = columnas_minusculas[col_cat]
                break

        # Buscar columna de emisor/receptor
        for col_emisor in self.COLUMNAS_EMISOR:
            if col_emisor in columnas_minusculas:
                mapeo['emisor_receptor'] = columnas_minusculas[col_emisor]
                break

        logger.info(f"📋 Columnas identificadas: {list(mapeo.keys())}")

        return mapeo

    def procesar_csv(self, ruta_archivo: str) -> List[Dict]:
        """
        Procesa un archivo CSV y extrae transacciones

        Args:
            ruta_archivo: Ruta al archivo CSV

        Returns:
            Lista de transacciones en formato estándar
        """
        try:
            # Leer CSV
            df = self.leer_csv(ruta_archivo)

            if df is None or df.empty:
                logger.warning(f"CSV vacío o inválido: {ruta_archivo}")
                return []

            # Identificar columnas
            mapeo = self.identificar_columnas(df)

            if 'monto' not in mapeo:
                logger.error("❌ No se encontró columna de monto en el CSV")
                return []

            logger.info(f"📊 Procesando {len(df)} filas del CSV...")

            transacciones = []

            for idx, row in df.iterrows():
                transaccion = self._extraer_transaccion(row, mapeo, ruta_archivo)

                if transaccion:
                    transacciones.append(transaccion)

            logger.info(f"✅ {len(transacciones)} transacciones extraídas del CSV")

            return transacciones

        except Exception as e:
            logger.error(f"❌ Error al procesar CSV {ruta_archivo}: {e}")
            return []

    def _extraer_transaccion(
        self,
        row: pd.Series,
        mapeo: Dict[str, str],
        ruta_archivo: str
    ) -> Optional[Dict]:
        """
        Extrae una transacción de una fila del DataFrame

        Args:
            row: Fila del DataFrame
            mapeo: Mapeo de columnas
            ruta_archivo: Ruta del archivo (para metadata)

        Returns:
            Diccionario con datos de la transacción o None si es inválida
        """
        try:
            # Extraer monto (obligatorio)
            monto = self._limpiar_monto(row[mapeo['monto']])

            if monto is None or monto == 0:
                return None

            # Determinar tipo: ingreso si monto positivo, egreso si negativo
            if monto > 0:
                tipo = "ingreso"
            else:
                tipo = "egreso"
                monto = abs(monto)  # Convertir a positivo

            # Extraer fecha (si existe)
            fecha = None
            if 'fecha' in mapeo:
                fecha = self._parsear_fecha(row[mapeo['fecha']])

            # Extraer descripción
            descripcion = ""
            if 'descripcion' in mapeo:
                descripcion = str(row[mapeo['descripcion']]) if pd.notna(row[mapeo['descripcion']]) else ""

            # Extraer categoría
            categoria = None
            if 'categoria' in mapeo:
                categoria = str(row[mapeo['categoria']]) if pd.notna(row[mapeo['categoria']]) else None

            # Extraer emisor/receptor
            emisor_receptor = None
            if 'emisor_receptor' in mapeo:
                emisor_receptor = str(row[mapeo['emisor_receptor']]) if pd.notna(row[mapeo['emisor_receptor']]) else None

            transaccion = {
                "tipo": tipo,
                "categoria": categoria,  # Puede ser None, se clasificará después
                "fecha": fecha,
                "monto": monto,
                "emisor_receptor": emisor_receptor,
                "descripcion": descripcion,
                "numero_comprobante": None,
                "origen": "csv",
                "archivo_origen": Path(ruta_archivo).name
            }

            return transaccion

        except Exception as e:
            logger.debug(f"Error al extraer transacción de fila: {e}")
            return None

    def _limpiar_monto(self, valor) -> Optional[float]:
        """
        Limpia y convierte un valor a float (monto)

        Args:
            valor: Valor a limpiar

        Returns:
            Float o None si no se puede convertir
        """
        try:
            if pd.isna(valor):
                return None

            # Convertir a string y limpiar
            valor_str = str(valor).strip()

            # Remover símbolos de moneda
            valor_str = valor_str.replace('$', '').replace('€', '').replace('£', '')
            valor_str = valor_str.replace('AR$', '').replace('USD', '').replace('ARS', '')

            # Remover espacios
            valor_str = valor_str.replace(' ', '')

            # Manejar separadores decimales (. o ,)
            # Si tiene ambos, asumir que el último es decimal
            if '.' in valor_str and ',' in valor_str:
                # Formato: 1,234.56 o 1.234,56
                if valor_str.rindex('.') > valor_str.rindex(','):
                    # Punto es decimal, coma es miles
                    valor_str = valor_str.replace(',', '')
                else:
                    # Coma es decimal, punto es miles
                    valor_str = valor_str.replace('.', '').replace(',', '.')
            elif ',' in valor_str:
                # Solo coma, podría ser decimal o miles
                # Si hay más de una coma, es separador de miles
                if valor_str.count(',') > 1:
                    valor_str = valor_str.replace(',', '')
                else:
                    # Asumir que es decimal
                    valor_str = valor_str.replace(',', '.')

            # Convertir a float
            monto = float(valor_str)

            return monto

        except Exception as e:
            logger.debug(f"Error al limpiar monto '{valor}': {e}")
            return None

    def _parsear_fecha(self, valor) -> Optional[str]:
        """
        Parsea una fecha y la convierte a formato YYYY-MM-DD

        Args:
            valor: Valor de fecha

        Returns:
            Fecha en formato ISO (YYYY-MM-DD) o None
        """
        try:
            if pd.isna(valor):
                return None

            # Intentar parsear con pandas
            fecha_dt = pd.to_datetime(valor, errors='coerce')

            if pd.isna(fecha_dt):
                return None

            return fecha_dt.strftime('%Y-%m-%d')

        except Exception as e:
            logger.debug(f"Error al parsear fecha '{valor}': {e}")
            return None


if __name__ == "__main__":
    # Prueba del módulo
    import sys

    if len(sys.argv) < 2:
        print("Uso: python csv_reader.py <ruta_archivo.csv>")
        exit(1)

    ruta = sys.argv[1]

    if not Path(ruta).exists():
        print(f"❌ Archivo no encontrado: {ruta}")
        exit(1)

    print(f"\n📄 Procesando CSV: {ruta}\n")

    reader = CSVReader()
    transacciones = reader.procesar_csv(ruta)

    print(f"✅ Total transacciones: {len(transacciones)}\n")

    # Mostrar primeras 5
    for i, t in enumerate(transacciones[:5], 1):
        print(f"{i}. {t['tipo'].upper()}: ${t['monto']:.2f}")
        print(f"   Descripción: {t['descripcion']}")
        print(f"   Fecha: {t['fecha']}")
        print(f"   Categoría: {t['categoria']}")
        print()

    if len(transacciones) > 5:
        print(f"... y {len(transacciones) - 5} más")
