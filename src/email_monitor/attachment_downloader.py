"""
Descargador de adjuntos de emails
Guarda archivos PDF, PNG, JPG y CSV en carpetas temporales
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from loguru import logger
import hashlib


class AttachmentDownloader:
    """Descarga y guarda adjuntos de emails en el sistema de archivos"""

    def __init__(self, base_dir: Path):
        """
        Inicializa el descargador de adjuntos

        Args:
            base_dir: Directorio base del proyecto
        """
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"

        # Carpetas de trabajo (antes de clasificar)
        self.temp_pdf_dir = self.data_dir / "temp_pdf"
        self.temp_img_dir = self.data_dir / "temp_img"
        self.temp_csv_dir = self.data_dir / "temp_csv"

        # Crear carpetas si no existen
        self._crear_carpetas()

    def _crear_carpetas(self):
        """Crea las carpetas necesarias para almacenar archivos"""
        carpetas = [
            self.temp_pdf_dir,
            self.temp_img_dir,
            self.temp_csv_dir,
        ]

        for carpeta in carpetas:
            carpeta.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Carpeta verificada: {carpeta}")

    def descargar_adjuntos_email(self, email_data: Dict) -> List[Dict]:
        """
        Descarga todos los adjuntos de un email

        Args:
            email_data: Diccionario con información del email y adjuntos

        Returns:
            Lista de diccionarios con información de archivos descargados
        """
        archivos_descargados = []

        try:
            email_id = email_data.get("id", "unknown")
            adjuntos = email_data.get("adjuntos", [])

            if not adjuntos:
                logger.warning(f"Email {email_id} sin adjuntos")
                return []

            logger.info(f"📥 Descargando {len(adjuntos)} adjuntos del email {email_id}")

            for adjunto in adjuntos:
                archivo_info = self._guardar_adjunto(adjunto, email_data)

                if archivo_info:
                    archivos_descargados.append(archivo_info)

            logger.info(f"✅ Descargados {len(archivos_descargados)} archivos")

        except Exception as e:
            logger.error(f"❌ Error al descargar adjuntos: {e}")

        return archivos_descargados

    def _guardar_adjunto(self, adjunto: Dict, email_data: Dict) -> Dict:
        """
        Guarda un adjunto individual en el sistema de archivos

        Args:
            adjunto: Diccionario con información del adjunto
            email_data: Información del email (para metadata)

        Returns:
            Diccionario con información del archivo guardado
        """
        try:
            filename = adjunto.get("filename", "sin_nombre")
            content = adjunto.get("content")

            if not content:
                logger.warning(f"Adjunto {filename} sin contenido")
                return None

            # Determinar tipo y carpeta destino
            tipo_archivo, carpeta_destino = self._determinar_tipo_archivo(filename)

            if not tipo_archivo:
                logger.warning(f"Tipo de archivo no soportado: {filename}")
                return None

            # Generar hash del contenido para detectar duplicados
            file_hash = hashlib.md5(content).hexdigest()

            # Crear nombre único: timestamp_hash_nombreoriginal
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_base = Path(filename).stem
            extension = Path(filename).suffix

            nombre_unico = f"{timestamp}_{file_hash[:8]}_{nombre_base}{extension}"
            ruta_completa = carpeta_destino / nombre_unico

            # Verificar si ya existe (por hash)
            if self._archivo_existe(carpeta_destino, file_hash):
                logger.info(f"⚠️  Archivo duplicado detectado: {filename}")
                return None

            # Guardar archivo
            with open(ruta_completa, "wb") as f:
                f.write(content)

            archivo_info = {
                "ruta": str(ruta_completa),
                "nombre_original": filename,
                "nombre_guardado": nombre_unico,
                "tipo": tipo_archivo,
                "hash": file_hash,
                "tamaño": len(content),
                "email_id": email_data.get("id"),
                "email_subject": email_data.get("subject"),
                "email_from": email_data.get("from"),
                "fecha_descarga": datetime.now().isoformat()
            }

            logger.info(f"✓ Guardado: {nombre_unico} ({len(content) / 1024:.1f} KB)")

            return archivo_info

        except Exception as e:
            logger.error(f"❌ Error al guardar adjunto {filename}: {e}")
            return None

    def _determinar_tipo_archivo(self, filename: str):
        """
        Determina el tipo de archivo y la carpeta destino

        Args:
            filename: Nombre del archivo

        Returns:
            Tupla (tipo, carpeta_destino) o (None, None) si no es válido
        """
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            return "pdf", self.temp_pdf_dir
        elif extension in [".png", ".jpg", ".jpeg"]:
            return "imagen", self.temp_img_dir
        elif extension == ".csv":
            return "csv", self.temp_csv_dir
        else:
            return None, None

    def _archivo_existe(self, carpeta: Path, file_hash: str) -> bool:
        """
        Verifica si un archivo con el mismo hash ya existe

        Args:
            carpeta: Carpeta donde buscar
            file_hash: Hash MD5 del archivo

        Returns:
            True si existe un archivo con ese hash
        """
        try:
            # Buscar archivos que contengan el hash en su nombre
            for archivo in carpeta.glob(f"*{file_hash[:8]}*"):
                return True
            return False

        except Exception as e:
            logger.error(f"Error al verificar duplicados: {e}")
            return False

    def obtener_archivos_pendientes(self) -> Dict[str, List[str]]:
        """
        Obtiene todos los archivos que aún no han sido procesados

        Returns:
            Diccionario con listas de archivos por tipo
        """
        archivos_pendientes = {
            "pdf": [str(f) for f in self.temp_pdf_dir.glob("*.pdf")],
            "imagenes": [str(f) for f in self.temp_img_dir.glob("*.png")] +
                       [str(f) for f in self.temp_img_dir.glob("*.jpg")] +
                       [str(f) for f in self.temp_img_dir.glob("*.jpeg")],
            "csv": [str(f) for f in self.temp_csv_dir.glob("*.csv")]
        }

        total = sum(len(v) for v in archivos_pendientes.values())
        logger.info(f"📊 Archivos pendientes de procesar: {total}")

        return archivos_pendientes

    def mover_archivo_procesado(self, ruta_archivo: str, tipo_transaccion: str):
        """
        Mueve un archivo ya procesado a la carpeta correspondiente

        Args:
            ruta_archivo: Ruta del archivo temporal
            tipo_transaccion: "ingreso" o "egreso"
        """
        try:
            archivo = Path(ruta_archivo)

            if not archivo.exists():
                logger.warning(f"Archivo no existe: {ruta_archivo}")
                return

            # Determinar carpeta destino
            if tipo_transaccion == "ingreso":
                carpeta_destino = self.data_dir / "ingresos"
            elif tipo_transaccion == "egreso":
                carpeta_destino = self.data_dir / "egresos"
            else:
                logger.error(f"Tipo de transacción inválido: {tipo_transaccion}")
                return

            carpeta_destino.mkdir(parents=True, exist_ok=True)

            # Mover archivo
            destino = carpeta_destino / archivo.name
            archivo.rename(destino)

            logger.info(f"✓ Archivo movido a {tipo_transaccion}: {archivo.name}")

        except Exception as e:
            logger.error(f"❌ Error al mover archivo: {e}")

    def limpiar_archivos_antiguos(self, dias: int = 30):
        """
        Elimina archivos procesados más antiguos que X días

        Args:
            dias: Número de días de antigüedad
        """
        from datetime import timedelta

        carpetas = [
            self.data_dir / "ingresos",
            self.data_dir / "egresos",
            self.data_dir / "procesados"
        ]

        archivos_eliminados = 0
        fecha_limite = datetime.now() - timedelta(days=dias)

        for carpeta in carpetas:
            if not carpeta.exists():
                continue

            for archivo in carpeta.glob("*"):
                if archivo.is_file():
                    # Obtener fecha de modificación
                    mtime = datetime.fromtimestamp(archivo.stat().st_mtime)

                    if mtime < fecha_limite:
                        try:
                            archivo.unlink()
                            archivos_eliminados += 1
                            logger.debug(f"🗑️  Eliminado: {archivo.name}")
                        except Exception as e:
                            logger.error(f"Error al eliminar {archivo.name}: {e}")

        logger.info(f"🗑️  Limpieza completada: {archivos_eliminados} archivos eliminados")


if __name__ == "__main__":
    # Prueba del módulo
    from pathlib import Path

    base = Path(__file__).parent.parent.parent
    downloader = AttachmentDownloader(base)

    # Simular descarga
    email_test = {
        "id": "12345",
        "subject": "Factura Edenor",
        "from": "facturacion@edenor.com.ar",
        "adjuntos": [
            {
                "filename": "factura_octubre.pdf",
                "content": b"PDF simulado contenido..."
            }
        ]
    }

    archivos = downloader.descargar_adjuntos_email(email_test)
    print(f"\n✅ Descargados: {len(archivos)} archivos\n")

    for archivo in archivos:
        print(f"  📄 {archivo['nombre_guardado']}")
        print(f"     Tipo: {archivo['tipo']}")
        print(f"     Tamaño: {archivo['tamaño']} bytes")
        print()

    # Ver pendientes
    pendientes = downloader.obtener_archivos_pendientes()
    print(f"📊 Archivos pendientes:")
    print(f"   PDF: {len(pendientes['pdf'])}")
    print(f"   Imágenes: {len(pendientes['imagenes'])}")
    print(f"   CSV: {len(pendientes['csv'])}")
