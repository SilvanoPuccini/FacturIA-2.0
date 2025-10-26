"""
Lector de documentos PDF e imágenes
Convierte documentos a formato procesable por la IA
"""
from pathlib import Path
from typing import Optional, List
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
from loguru import logger
import io


class DocumentReader:
    """Lee y procesa documentos PDF e imágenes para análisis con IA"""

    @staticmethod
    def leer_imagen(ruta_archivo: str) -> Optional[Image.Image]:
        """
        Lee una imagen desde archivo

        Args:
            ruta_archivo: Ruta al archivo de imagen

        Returns:
            Objeto PIL Image o None si hay error
        """
        try:
            imagen = Image.open(ruta_archivo)

            # Convertir a RGB si es necesario (algunas imágenes son RGBA)
            if imagen.mode != "RGB":
                imagen = imagen.convert("RGB")

            logger.info(f"✓ Imagen leída: {Path(ruta_archivo).name} ({imagen.size})")
            return imagen

        except Exception as e:
            logger.error(f"❌ Error al leer imagen {ruta_archivo}: {e}")
            return None

    @staticmethod
    def pdf_a_imagenes(ruta_pdf: str, dpi: int = 200) -> List[Image.Image]:
        """
        Convierte un PDF a lista de imágenes (una por página)

        Args:
            ruta_pdf: Ruta al archivo PDF
            dpi: Resolución de conversión (mayor = mejor calidad pero más lento)

        Returns:
            Lista de objetos PIL Image
        """
        try:
            logger.info(f"📄 Convirtiendo PDF a imágenes: {Path(ruta_pdf).name}")

            # Convertir PDF a imágenes
            imagenes = convert_from_path(ruta_pdf, dpi=dpi)

            logger.info(f"✓ PDF convertido: {len(imagenes)} página(s)")
            return imagenes

        except Exception as e:
            logger.error(f"❌ Error al convertir PDF {ruta_pdf}: {e}")
            return []

    @staticmethod
    def extraer_texto_pdf(ruta_pdf: str) -> str:
        """
        Intenta extraer texto directamente del PDF (OCR no incluido)

        Args:
            ruta_pdf: Ruta al archivo PDF

        Returns:
            Texto extraído del PDF
        """
        try:
            texto_completo = ""

            with open(ruta_pdf, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)

                for pagina_num in range(len(pdf_reader.pages)):
                    pagina = pdf_reader.pages[pagina_num]
                    texto_completo += pagina.extract_text() + "\n"

            logger.info(f"✓ Texto extraído del PDF: {len(texto_completo)} caracteres")
            return texto_completo.strip()

        except Exception as e:
            logger.error(f"❌ Error al extraer texto del PDF {ruta_pdf}: {e}")
            return ""

    @staticmethod
    def procesar_documento(ruta_archivo: str) -> dict:
        """
        Procesa un documento (PDF o imagen) y lo prepara para la IA

        Args:
            ruta_archivo: Ruta al archivo

        Returns:
            Diccionario con información del documento procesado
        """
        archivo = Path(ruta_archivo)
        extension = archivo.suffix.lower()

        resultado = {
            "ruta": ruta_archivo,
            "nombre": archivo.name,
            "tipo": None,
            "imagenes": [],
            "texto_extraido": "",
            "valido": False
        }

        try:
            if extension == ".pdf":
                resultado["tipo"] = "pdf"

                # Intentar extraer texto primero
                texto = DocumentReader.extraer_texto_pdf(ruta_archivo)
                resultado["texto_extraido"] = texto

                # Convertir a imágenes para Gemini Vision
                imagenes = DocumentReader.pdf_a_imagenes(ruta_archivo)
                resultado["imagenes"] = imagenes
                resultado["valido"] = len(imagenes) > 0

            elif extension in [".png", ".jpg", ".jpeg"]:
                resultado["tipo"] = "imagen"

                # Cargar imagen
                imagen = DocumentReader.leer_imagen(ruta_archivo)

                if imagen:
                    resultado["imagenes"] = [imagen]
                    resultado["valido"] = True

            else:
                logger.warning(f"Tipo de archivo no soportado: {extension}")

            if resultado["valido"]:
                logger.info(f"✅ Documento procesado: {archivo.name}")
            else:
                logger.warning(f"⚠️  No se pudo procesar: {archivo.name}")

            return resultado

        except Exception as e:
            logger.error(f"❌ Error al procesar documento {ruta_archivo}: {e}")
            resultado["valido"] = False
            return resultado

    @staticmethod
    def optimizar_imagen(imagen: Image.Image, max_size: int = 1024) -> Image.Image:
        """
        Optimiza una imagen para enviar a la API (reduce tamaño si es muy grande)

        Args:
            imagen: Imagen PIL
            max_size: Tamaño máximo del lado más largo

        Returns:
            Imagen optimizada
        """
        try:
            # Si la imagen es muy grande, reducirla manteniendo aspect ratio
            width, height = imagen.size

            if max(width, height) > max_size:
                ratio = max_size / max(width, height)
                nuevo_width = int(width * ratio)
                nuevo_height = int(height * ratio)

                imagen = imagen.resize((nuevo_width, nuevo_height), Image.Resampling.LANCZOS)
                logger.debug(f"Imagen redimensionada: {width}x{height} -> {nuevo_width}x{nuevo_height}")

            return imagen

        except Exception as e:
            logger.error(f"Error al optimizar imagen: {e}")
            return imagen

    @staticmethod
    def imagen_a_bytes(imagen: Image.Image, formato: str = "PNG") -> bytes:
        """
        Convierte una imagen PIL a bytes

        Args:
            imagen: Imagen PIL
            formato: Formato de salida (PNG, JPEG)

        Returns:
            Bytes de la imagen
        """
        try:
            buffer = io.BytesIO()
            imagen.save(buffer, format=formato)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error al convertir imagen a bytes: {e}")
            return b""


if __name__ == "__main__":
    # Prueba del módulo
    import sys

    if len(sys.argv) < 2:
        print("Uso: python document_reader.py <ruta_archivo>")
        exit(1)

    ruta = sys.argv[1]

    if not Path(ruta).exists():
        print(f"❌ Archivo no encontrado: {ruta}")
        exit(1)

    print(f"\n📄 Procesando documento: {ruta}\n")

    resultado = DocumentReader.procesar_documento(ruta)

    print(f"Tipo: {resultado['tipo']}")
    print(f"Válido: {resultado['valido']}")
    print(f"Imágenes: {len(resultado['imagenes'])}")
    print(f"Texto extraído: {len(resultado['texto_extraido'])} caracteres")

    if resultado['texto_extraido']:
        print(f"\nPrimeros 200 caracteres del texto:")
        print(resultado['texto_extraido'][:200])
