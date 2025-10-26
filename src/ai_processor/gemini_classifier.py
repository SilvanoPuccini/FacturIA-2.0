"""
Clasificador de documentos financieros usando Google Gemini Vision
Analiza imágenes/PDFs y extrae información estructurada
"""
import google.generativeai as genai
from PIL import Image
from typing import Dict, Optional, List
import json
from loguru import logger
import sys

# Configurar logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/ai_processor.log", rotation="10 MB", level="DEBUG")


class GeminiClassifier:
    """Clasificador de documentos financieros usando Gemini Vision"""

    def __init__(self, api_key: str, prompt_template: str):
        """
        Inicializa el clasificador Gemini

        Args:
            api_key: API key de Google Gemini
            prompt_template: Template del prompt para clasificación
        """
        self.api_key = api_key
        self.prompt_template = prompt_template

        # Configurar Gemini
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ Gemini Vision configurado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al configurar Gemini: {e}")
            raise

    def clasificar_imagen(self, imagen: Image.Image, contexto: str = "") -> Optional[Dict]:
        """
        Clasifica una imagen de documento financiero

        Args:
            imagen: Imagen PIL del documento
            contexto: Contexto adicional (ej: nombre del archivo, remitente)

        Returns:
            Diccionario con datos extraídos o None si falla
        """
        try:
            # Preparar prompt
            prompt = self.prompt_template

            if contexto:
                prompt = f"Contexto adicional: {contexto}\n\n{prompt}"

            logger.info("🤖 Enviando imagen a Gemini Vision...")

            # Llamar a Gemini Vision
            response = self.model.generate_content([prompt, imagen])

            # Extraer texto de respuesta
            texto_respuesta = response.text.strip()

            logger.debug(f"Respuesta cruda de Gemini: {texto_respuesta[:200]}...")

            # Parsear JSON
            datos_extraidos = self._parsear_respuesta(texto_respuesta)

            if datos_extraidos:
                logger.info(f"✅ Documento clasificado: {datos_extraidos.get('tipo')} - {datos_extraidos.get('categoria')}")
                return datos_extraidos
            else:
                logger.warning("⚠️  No se pudo extraer datos válidos de la respuesta")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error al parsear JSON de Gemini: {e}")
            logger.error(f"Respuesta: {texto_respuesta}")
            return None

        except Exception as e:
            logger.error(f"❌ Error al clasificar imagen: {e}")
            return None

    def clasificar_documento(
        self,
        imagenes: List[Image.Image],
        texto_extraido: str = "",
        contexto: str = ""
    ) -> Optional[Dict]:
        """
        Clasifica un documento que puede tener múltiples páginas

        Args:
            imagenes: Lista de imágenes del documento
            texto_extraido: Texto extraído del PDF (si aplica)
            contexto: Contexto adicional

        Returns:
            Diccionario con datos extraídos
        """
        if not imagenes:
            logger.warning("No hay imágenes para procesar")
            return None

        # Por ahora, procesar solo la primera página
        # TODO: En el futuro, combinar información de múltiples páginas
        primera_pagina = imagenes[0]

        # Agregar texto extraído al contexto si existe
        if texto_extraido:
            contexto = f"{contexto}\nTexto extraído del PDF:\n{texto_extraido[:500]}"

        return self.clasificar_imagen(primera_pagina, contexto)

    def _parsear_respuesta(self, texto_respuesta: str) -> Optional[Dict]:
        """
        Parsea la respuesta de Gemini y extrae el JSON

        Args:
            texto_respuesta: Texto crudo de la respuesta

        Returns:
            Diccionario con datos o None si no se puede parsear
        """
        try:
            # Limpiar texto: remover markdown code blocks si existen
            texto_limpio = texto_respuesta.strip()

            if texto_limpio.startswith("```json"):
                texto_limpio = texto_limpio[7:]  # Remover ```json
            elif texto_limpio.startswith("```"):
                texto_limpio = texto_limpio[3:]  # Remover ```

            if texto_limpio.endswith("```"):
                texto_limpio = texto_limpio[:-3]

            texto_limpio = texto_limpio.strip()

            # Parsear JSON
            datos = json.loads(texto_limpio)

            # Validar campos obligatorios
            campos_requeridos = ["tipo", "categoria", "monto"]
            for campo in campos_requeridos:
                if campo not in datos:
                    logger.warning(f"Campo requerido faltante: {campo}")
                    return None

            # Validar tipo
            if datos["tipo"] not in ["ingreso", "egreso"]:
                logger.warning(f"Tipo inválido: {datos['tipo']}")
                return None

            return datos

        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON: {e}")
            logger.debug(f"Texto que falló: {texto_limpio}")
            return None

        except Exception as e:
            logger.error(f"Error al parsear respuesta: {e}")
            return None

    def validar_clasificacion(self, datos: Dict, categorias_validas: Dict) -> bool:
        """
        Valida que la clasificación sea correcta

        Args:
            datos: Datos extraídos por Gemini
            categorias_validas: Dict con listas de categorías válidas por tipo

        Returns:
            True si la clasificación es válida
        """
        try:
            tipo = datos.get("tipo")
            categoria = datos.get("categoria")

            if not tipo or not categoria:
                return False

            # Validar categoría según tipo
            if tipo == "ingreso":
                categorias = categorias_validas.get("ingresos", [])
            elif tipo == "egreso":
                categorias = categorias_validas.get("egresos", [])
            else:
                return False

            if categoria not in categorias:
                logger.warning(f"Categoría inválida '{categoria}' para tipo '{tipo}'")
                return False

            # Validar monto
            monto = datos.get("monto")
            if monto is None or not isinstance(monto, (int, float)) or monto <= 0:
                logger.warning(f"Monto inválido: {monto}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error al validar clasificación: {e}")
            return False

    def procesar_batch(
        self,
        documentos: List[Dict],
        max_reintentos: int = 2
    ) -> List[Dict]:
        """
        Procesa un lote de documentos

        Args:
            documentos: Lista de documentos procesados por DocumentReader
            max_reintentos: Reintentos máximos por documento

        Returns:
            Lista de resultados con clasificaciones
        """
        resultados = []

        for idx, doc in enumerate(documentos, 1):
            logger.info(f"📄 Procesando documento {idx}/{len(documentos)}: {doc.get('nombre')}")

            if not doc.get("valido"):
                logger.warning(f"Documento inválido, saltando: {doc.get('nombre')}")
                continue

            imagenes = doc.get("imagenes", [])
            texto = doc.get("texto_extraido", "")
            contexto = f"Archivo: {doc.get('nombre')}"

            # Intentar clasificar con reintentos
            clasificacion = None
            for intento in range(max_reintentos):
                clasificacion = self.clasificar_documento(imagenes, texto, contexto)

                if clasificacion:
                    break

                if intento < max_reintentos - 1:
                    logger.warning(f"Reintentando clasificación... ({intento + 1}/{max_reintentos})")

            resultado = {
                "ruta": doc.get("ruta"),
                "nombre": doc.get("nombre"),
                "tipo_archivo": doc.get("tipo"),
                "clasificacion": clasificacion,
                "exito": clasificacion is not None
            }

            resultados.append(resultado)

        exitosos = sum(1 for r in resultados if r["exito"])
        logger.info(f"✅ Batch completado: {exitosos}/{len(documentos)} exitosos")

        return resultados


if __name__ == "__main__":
    # Prueba del módulo
    from dotenv import load_dotenv
    import os
    from pathlib import Path

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("❌ Falta GOOGLE_API_KEY en .env")
        exit(1)

    # Prompt de prueba
    prompt = """
Analiza esta imagen financiera y responde en JSON:

{
  "tipo": "ingreso" o "egreso",
  "categoria": "...",
  "monto": 1234.56,
  "emisor_receptor": "...",
  "fecha": "YYYY-MM-DD",
  "descripcion": "..."
}
"""

    classifier = GeminiClassifier(api_key, prompt)

    # Probar con una imagen de prueba (si existe)
    test_image = Path("test_factura.png")

    if test_image.exists():
        from PIL import Image
        img = Image.open(test_image)
        resultado = classifier.clasificar_imagen(img, "Factura de prueba")

        print("\n📊 Resultado:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        print("ℹ️  No hay imagen de prueba. Coloca 'test_factura.png' en el directorio.")
