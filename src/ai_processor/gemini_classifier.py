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
import time
from functools import wraps

# Configurar logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/ai_processor.log", rotation="10 MB", level="DEBUG")


class GeminiClassifier:
    """Clasificador de documentos financieros usando Gemini Vision"""

    def __init__(self, api_key: str, prompt_template: str, timeout: int = 60, max_reintentos: int = 3):
        """
        Inicializa el clasificador Gemini

        Args:
            api_key: API key de Google Gemini
            prompt_template: Template del prompt para clasificación
            timeout: Timeout para llamadas a API en segundos (default: 60)
            max_reintentos: Número máximo de reintentos en caso de fallo (default: 3)
        """
        self.api_key = api_key
        self.prompt_template = prompt_template
        self.timeout = timeout
        self.max_reintentos = max_reintentos
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 10  # Aumentado de 5 a 10 para más tolerancia
        self._circuit_breaker_reset_time = None

        # Configurar Gemini
        try:
            genai.configure(api_key=api_key)

            # Configurar generación con timeout implícito
            generation_config = {
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 1024,
            }

            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',  # Gemini 2.0: 15 RPM (1 cada 4s)
                generation_config=generation_config
            )
            logger.info("✅ Gemini Vision configurado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al configurar Gemini: {e}")
            raise

    def _verificar_circuit_breaker(self) -> bool:
        """
        Verifica si el circuit breaker está abierto (demasiados fallos)

        Returns:
            True si se puede continuar, False si el circuit breaker está abierto
        """
        # Si hay un tiempo de reset, verificar si ya pasó
        if self._circuit_breaker_reset_time:
            if time.time() > self._circuit_breaker_reset_time:
                logger.info("🔄 Circuit breaker: reiniciando contador de fallos")
                self._circuit_breaker_failures = 0
                self._circuit_breaker_reset_time = None
            else:
                tiempo_restante = int(self._circuit_breaker_reset_time - time.time())
                logger.warning(f"⚡ Circuit breaker ABIERTO - esperando {tiempo_restante}s antes de reintentar")
                return False

        # Si alcanzamos el umbral, abrir el circuit breaker
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            self._circuit_breaker_reset_time = time.time() + 120  # Esperar 120 segundos
            logger.error(f"⚡ Circuit breaker ABIERTO por {self._circuit_breaker_failures} fallos consecutivos")
            return False

        return True

    def _registrar_exito_api(self):
        """Registra un llamado exitoso a la API"""
        if self._circuit_breaker_failures > 0:
            logger.info(f"✅ API recuperada - reseteando circuit breaker ({self._circuit_breaker_failures} fallos)")
        self._circuit_breaker_failures = 0
        self._circuit_breaker_reset_time = None

    def _registrar_fallo_api(self):
        """Registra un fallo en la API"""
        self._circuit_breaker_failures += 1
        logger.warning(f"⚠️ Fallo API registrado ({self._circuit_breaker_failures}/{self._circuit_breaker_threshold})")

    def _llamar_gemini_con_reintentos(self, prompt: str, imagen: Image.Image) -> Optional[str]:
        """
        Llama a Gemini con reintentos y backoff exponencial

        Args:
            prompt: Prompt para Gemini
            imagen: Imagen a analizar

        Returns:
            Texto de respuesta o None si falla
        """
        # Verificar circuit breaker
        if not self._verificar_circuit_breaker():
            return None

        for intento in range(1, self.max_reintentos + 1):
            try:
                logger.info(f"🤖 Llamando a Gemini Vision (intento {intento}/{self.max_reintentos})...")

                # Llamar a Gemini (la API de Google no tiene timeout directo, pero podemos usar signal o threading)
                response = self.model.generate_content([prompt, imagen])

                # Si llegamos aquí, fue exitoso
                self._registrar_exito_api()
                return response.text.strip()

            except Exception as e:
                error_msg = str(e).lower()

                # Rate limiting
                if "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
                    logger.warning(f"⏱️ Rate limit alcanzado (intento {intento}/{self.max_reintentos})")
                    self._registrar_fallo_api()
                    if intento < self.max_reintentos:
                        wait_time = min(10 * intento, 60)  # 10s, 20s, 30s... máx 60s
                        logger.info(f"⏳ Esperando {wait_time}s por rate limit...")
                        time.sleep(wait_time)
                        continue

                # Timeout o error de red
                elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
                    logger.warning(f"🌐 Error de conexión/timeout (intento {intento}/{self.max_reintentos}): {e}")
                    self._registrar_fallo_api()
                    if intento < self.max_reintentos:
                        wait_time = 2 ** intento  # Backoff exponencial
                        logger.info(f"⏳ Esperando {wait_time}s antes de reintentar...")
                        time.sleep(wait_time)
                        continue

                # Error de API (500, 503, etc.)
                elif "500" in error_msg or "503" in error_msg or "unavailable" in error_msg:
                    logger.warning(f"⚠️ API temporalmente no disponible (intento {intento}/{self.max_reintentos})")
                    self._registrar_fallo_api()
                    if intento < self.max_reintentos:
                        wait_time = 2 ** intento
                        logger.info(f"⏳ Esperando {wait_time}s antes de reintentar...")
                        time.sleep(wait_time)
                        continue

                # Otro error
                else:
                    logger.error(f"❌ Error en Gemini API: {type(e).__name__}: {e}")
                    self._registrar_fallo_api()
                    if intento < self.max_reintentos:
                        wait_time = 2 ** intento
                        time.sleep(wait_time)
                        continue

                # Si llegamos aquí en el último intento, retornar None
                if intento == self.max_reintentos:
                    logger.error(f"❌ Máximo de reintentos alcanzado para Gemini API")
                    return None

        return None

    def clasificar_imagen(self, imagen: Image.Image, contexto: str = "", categorias_validas: Optional[Dict] = None) -> Optional[Dict]:
        """
        Clasifica una imagen de documento financiero

        Args:
            imagen: Imagen PIL del documento
            contexto: Contexto adicional (ej: nombre del archivo, remitente)
            categorias_validas: Dict con categorías válidas {'ingresos': [...], 'egresos': [...]}

        Returns:
            Diccionario con datos extraídos o None si falla
        """
        try:
            # Preparar prompt
            prompt = self.prompt_template

            if contexto:
                prompt = f"Contexto adicional: {contexto}\n\n{prompt}"

            # Llamar a Gemini Vision con reintentos y backoff
            texto_respuesta = self._llamar_gemini_con_reintentos(prompt, imagen)

            if not texto_respuesta:
                logger.warning("⚠️ No se obtuvo respuesta de Gemini después de reintentos")
                return None

            logger.debug(f"Respuesta cruda de Gemini: {texto_respuesta[:200]}...")

            # Parsear JSON
            datos_extraidos = self._parsear_respuesta(texto_respuesta)

            if not datos_extraidos:
                logger.warning("⚠️  No se pudo extraer datos válidos de la respuesta")
                return None

            # Validar y corregir si se proporcionaron categorías válidas
            if categorias_validas:
                datos_extraidos = self._validar_y_corregir_datos(datos_extraidos, categorias_validas)

                if not datos_extraidos:
                    logger.warning("⚠️ Datos inválidos después de validación")
                    return None

            logger.info(f"✅ Documento clasificado: {datos_extraidos.get('tipo')} - {datos_extraidos.get('categoria')} - ${datos_extraidos.get('monto')}")

            # Marcar si requiere revisión manual (baja confianza)
            if datos_extraidos.get('requiere_revision'):
                logger.warning(f"⚠️ Transacción marcada para revisión manual: {datos_extraidos.get('razon_revision')}")

            return datos_extraidos

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error al parsear JSON de Gemini: {e}")
            logger.error(f"Respuesta: {texto_respuesta if 'texto_respuesta' in locals() else 'N/A'}")
            return None

        except Exception as e:
            logger.error(f"❌ Error al clasificar imagen: {type(e).__name__}: {e}")
            return None

    def clasificar_documento(
        self,
        imagenes: List[Image.Image],
        texto_extraido: str = "",
        contexto: str = "",
        categorias_validas: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Clasifica un documento que puede tener múltiples páginas

        Args:
            imagenes: Lista de imágenes del documento
            texto_extraido: Texto extraído del PDF (si aplica)
            contexto: Contexto adicional
            categorias_validas: Dict con categorías válidas {'ingresos': [...], 'egresos': [...]}

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

        return self.clasificar_imagen(primera_pagina, contexto, categorias_validas)

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

            # Estrategia 1: Intentar parsear JSON normal
            try:
                datos = json.loads(texto_limpio)
            except json.JSONDecodeError:
                # Estrategia 2: Reemplazar comillas simples por dobles
                # Pero con cuidado para no romper strings que contengan apóstrofes
                import re
                # Buscar el patrón de JSON con comillas simples
                texto_corregido = texto_limpio.replace("'", '"')
                try:
                    datos = json.loads(texto_corregido)
                except json.JSONDecodeError:
                    # Estrategia 3: Intentar extraer con regex (último recurso)
                    logger.warning("Usando extracción por regex como último recurso")
                    import ast
                    try:
                        datos = ast.literal_eval(texto_limpio)
                    except:
                        raise json.JSONDecodeError("No se pudo parsear con ninguna estrategia", texto_limpio, 0)

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
            logger.error(f"TEXTO ORIGINAL:\n{'='*60}\n{texto_respuesta}\n{'='*60}")
            logger.error(f"TEXTO LIMPIO:\n{'='*60}\n{texto_limpio}\n{'='*60}")
            return None

        except Exception as e:
            logger.error(f"Error al parsear respuesta: {e}")
            return None

    def _validar_y_corregir_datos(self, datos: Dict, categorias_validas: Dict) -> Optional[Dict]:
        """
        Valida y corrige automáticamente los datos extraídos

        Args:
            datos: Datos extraídos por Gemini
            categorias_validas: Dict con categorías válidas {'ingresos': [...], 'egresos': [...]}

        Returns:
            Datos corregidos o None si no se pueden corregir
        """
        try:
            datos_corregidos = datos.copy()
            requiere_revision = False
            razones_revision = []

            # Validar tipo
            tipo = datos_corregidos.get("tipo", "").lower().strip()
            if tipo not in ["ingreso", "egreso"]:
                logger.error(f"❌ Tipo inválido: '{tipo}'")
                return None

            datos_corregidos["tipo"] = tipo

            # Obtener categorías válidas según el tipo
            if tipo == "ingreso":
                categorias = categorias_validas.get("ingresos", [])
            else:
                categorias = categorias_validas.get("egresos", [])

            # Validar y corregir categoría
            categoria_original = datos_corregidos.get("categoria", "").lower().strip()
            categoria_corregida = self._corregir_categoria(categoria_original, categorias)

            if not categoria_corregida:
                logger.error(f"❌ No se pudo corregir categoría: '{categoria_original}'")
                requiere_revision = True
                razones_revision.append(f"Categoría desconocida: {categoria_original}")
                # Usar categoría por defecto
                categoria_corregida = "otro_egreso" if tipo == "egreso" else "otro_ingreso"

            if categoria_corregida != categoria_original:
                logger.warning(f"🔧 Categoría corregida: '{categoria_original}' → '{categoria_corregida}'")

            datos_corregidos["categoria"] = categoria_corregida

            # Validar y corregir monto
            monto = datos_corregidos.get("monto")
            if monto is None:
                logger.error("❌ Monto es null")
                return None

            # Convertir string a número si es necesario
            if isinstance(monto, str):
                # Remover símbolos de moneda y espacios
                monto_limpio = monto.replace("$", "").replace("AR$", "").replace(" ", "").replace(".", "").replace(",", ".")
                try:
                    monto = float(monto_limpio)
                    logger.info(f"🔧 Monto convertido de string: '{datos_corregidos.get('monto')}' → {monto}")
                except ValueError:
                    logger.error(f"❌ No se puede convertir monto: '{datos_corregidos.get('monto')}'")
                    return None

            if not isinstance(monto, (int, float)) or monto <= 0:
                logger.error(f"❌ Monto inválido: {monto}")
                return None

            datos_corregidos["monto"] = float(monto)

            # Validar fecha
            fecha = datos_corregidos.get("fecha")
            if fecha:
                # Validar formato YYYY-MM-DD
                import re
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(fecha)):
                    logger.warning(f"⚠️ Formato de fecha inválido: {fecha}")
                    requiere_revision = True
                    razones_revision.append(f"Fecha con formato incorrecto: {fecha}")

            # Marcar para revisión si es necesario
            datos_corregidos["requiere_revision"] = requiere_revision
            datos_corregidos["razon_revision"] = ", ".join(razones_revision) if razones_revision else None
            datos_corregidos["procesado_por_ia"] = True
            datos_corregidos["confianza_clasificacion"] = 0.5 if requiere_revision else 0.9

            return datos_corregidos

        except Exception as e:
            logger.error(f"❌ Error al validar y corregir datos: {e}")
            return None

    def _corregir_categoria(self, categoria: str, categorias_validas: List[str]) -> Optional[str]:
        """
        Intenta corregir una categoría usando similitud de texto

        Args:
            categoria: Categoría a corregir
            categorias_validas: Lista de categorías válidas

        Returns:
            Categoría corregida o None si no se puede corregir
        """
        if not categoria:
            return None

        categoria_lower = categoria.lower().strip()

        # Primero, verificar coincidencia exacta
        if categoria_lower in categorias_validas:
            return categoria_lower

        # Mapeo de sinónimos y variaciones comunes
        mapeo_sinonimos = {
            # Servicios
            "servicios": "factura_servicios",
            "factura servicios": "factura_servicios",
            "facturas": "factura_servicios",
            "luz": "factura_servicios",
            "agua": "factura_servicios",
            "gas": "factura_servicios",
            "internet": "factura_servicios",
            "telefono": "factura_servicios",
            "celular": "factura_servicios",

            # Supermercado
            "super": "supermercado",
            "compras": "supermercado",
            "alimentos": "supermercado",
            "mercado": "supermercado",

            # Impuestos
            "impuesto": "impuestos",
            "abl": "impuestos",
            "patente": "impuestos",
            "ganancias": "impuestos",

            # Salud
            "medico": "salud",
            "farmacia": "salud",
            "medicina": "salud",
            "prepaga": "salud",
            "obra social": "salud",

            # Entretenimiento
            "cine": "entretenimiento",
            "restaurante": "entretenimiento",
            "delivery": "entretenimiento",
            "ocio": "entretenimiento",

            # Ingresos
            "salario": "sueldo",
            "pago": "sueldo",
            "honorarios": "cobro_servicios",
            "factura": "cobro_servicios",
            "transferencia": "transferencia_recibida",
            "venta": "ventas",
        }

        # Intentar mapeo directo
        if categoria_lower in mapeo_sinonimos:
            categoria_mapeada = mapeo_sinonimos[categoria_lower]
            if categoria_mapeada in categorias_validas:
                return categoria_mapeada

        # Búsqueda por substring (ej: "factura_de_servicios" → "factura_servicios")
        for valida in categorias_validas:
            if valida in categoria_lower or categoria_lower in valida:
                return valida

        # Si no hay coincidencia, devolver None
        return None

    def validar_clasificacion(self, datos: Dict, categorias_validas: Dict) -> bool:
        """
        Valida que la clasificación sea correcta (versión legacy)

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
        documentos: List[Dict]
    ) -> List[Dict]:
        """
        Procesa un lote de documentos

        Args:
            documentos: Lista de documentos procesados por DocumentReader

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

            # Clasificar (los reintentos ya están manejados internamente)
            clasificacion = self.clasificar_documento(imagenes, texto, contexto)

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
