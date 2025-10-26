#!/usr/bin/env python3
"""
FacturIA 2.0 - Sistema de Gestión Financiera Automatizado
Script principal que orquesta todos los módulos

Flujo:
1. Monitorea emails nuevos
2. Descarga adjuntos (PDF, PNG, JPG, CSV)
3. Procesa con IA (PDF/PNG) o directamente (CSV)
4. Almacena en base de datos
5. Dashboard disponible en tiempo real
"""
import schedule
import time
from datetime import datetime
from pathlib import Path
from loguru import logger
import sys
import os
import hashlib

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    GOOGLE_API_KEY,
    GMAIL_EMAIL,
    GMAIL_PASSWORD,
    EMAIL_CHECK_INTERVAL,
    GEMINI_PROMPT_TEMPLATE,
    CATEGORIAS_INGRESOS,
    CATEGORIAS_EGRESOS,
    validar_configuracion
)

from src.email_monitor import GmailReader, AttachmentDownloader
from src.ai_processor import DocumentReader, GeminiClassifier
from src.csv_processor import CSVReader, DataTransformer
from src.database import (
    inicializar_base_datos,
    crear_transacciones_batch,
    registrar_archivo_procesado,
    archivo_ya_procesado
)

# Configurar logger
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add("logs/facturia2_{time:YYYY-MM-DD}.log", rotation="500 MB", retention="30 days", level="DEBUG")

BASE_DIR = Path(__file__).parent


class FacturiaOrchestrator:
    """Orquestador principal del sistema FacturIA 2.0"""

    def __init__(self):
        """Inicializa el orquestador"""
        logger.info("🚀 Inicializando FacturIA 2.0...")

        # Validar configuración
        if not validar_configuracion():
            logger.error("❌ Configuración inválida. Abortando.")
            sys.exit(1)

        # Inicializar componentes
        self.gmail_reader = GmailReader(GMAIL_EMAIL, GMAIL_PASSWORD)
        self.downloader = AttachmentDownloader(BASE_DIR)
        self.csv_reader = CSVReader()
        self.transformer = DataTransformer(CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS)

        # Inicializar IA
        try:
            self.classifier = GeminiClassifier(GOOGLE_API_KEY, GEMINI_PROMPT_TEMPLATE)
            self.ia_disponible = True
        except Exception as e:
            logger.warning(f"⚠️  No se pudo inicializar Gemini: {e}")
            logger.warning("El sistema funcionará solo con CSV")
            self.ia_disponible = False

        # Inicializar base de datos
        self.db = inicializar_base_datos()

        logger.info("✅ FacturIA 2.0 inicializado correctamente")

    def ciclo_completo(self):
        """Ejecuta un ciclo completo de procesamiento"""
        try:
            logger.info("\n" + "="*60)
            logger.info(f"📧 Iniciando ciclo de procesamiento - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*60 + "\n")

            # 1. Leer emails no leídos
            emails = self.leer_emails()

            if not emails:
                logger.info("📭 No hay emails nuevos con adjuntos")
                return

            # 2. Descargar adjuntos
            archivos_descargados = self.descargar_adjuntos(emails)

            if not archivos_descargados:
                logger.info("No hay archivos nuevos para procesar")
                return

            # 3. Procesar archivos
            transacciones = self.procesar_archivos(archivos_descargados)

            # 4. Guardar en base de datos
            self.guardar_transacciones(transacciones)

            logger.info(f"\n✅ Ciclo completado: {len(transacciones)} transacciones procesadas\n")

        except Exception as e:
            logger.error(f"❌ Error en ciclo de procesamiento: {e}")
            logger.exception(e)

    def leer_emails(self):
        """Lee emails no leídos con adjuntos"""
        try:
            if not self.gmail_reader.connected:
                self.gmail_reader.conectar()

            emails = self.gmail_reader.obtener_emails_no_leidos()

            logger.info(f"📬 {len(emails)} emails con adjuntos encontrados")

            return emails

        except Exception as e:
            logger.error(f"❌ Error al leer emails: {e}")
            return []

    def descargar_adjuntos(self, emails):
        """Descarga adjuntos de los emails"""
        archivos_descargados = []

        for email_data in emails:
            try:
                archivos = self.downloader.descargar_adjuntos_email(email_data)
                archivos_descargados.extend(archivos)

                # Marcar email como leído
                self.gmail_reader.marcar_como_leido(email_data['id'])

            except Exception as e:
                logger.error(f"Error al procesar email {email_data.get('id')}: {e}")
                continue

        logger.info(f"📥 {len(archivos_descargados)} archivos descargados")

        return archivos_descargados

    def procesar_archivos(self, archivos):
        """Procesa todos los archivos descargados"""
        transacciones_totales = []

        # Separar por tipo
        archivos_pdf_img = [a for a in archivos if a['tipo'] in ['pdf', 'imagen']]
        archivos_csv = [a for a in archivos if a['tipo'] == 'csv']

        # Procesar PDF/IMG con IA
        if archivos_pdf_img and self.ia_disponible:
            logger.info(f"🤖 Procesando {len(archivos_pdf_img)} archivos con IA...")
            transacciones_ia = self.procesar_con_ia(archivos_pdf_img)
            transacciones_totales.extend(transacciones_ia)

        # Procesar CSV directamente
        if archivos_csv:
            logger.info(f"📊 Procesando {len(archivos_csv)} archivos CSV...")
            transacciones_csv = self.procesar_csv(archivos_csv)
            transacciones_totales.extend(transacciones_csv)

        return transacciones_totales

    def procesar_con_ia(self, archivos):
        """Procesa archivos PDF/imagen con Gemini Vision"""
        transacciones = []

        for archivo_info in archivos:
            try:
                ruta = archivo_info['ruta']
                file_hash = archivo_info['hash']

                # Verificar si ya fue procesado
                with self.db.get_session() as session:
                    if archivo_ya_procesado(session, file_hash):
                        logger.info(f"⏭️  Archivo ya procesado (hash): {archivo_info['nombre_guardado']}")
                        continue

                # Procesar documento
                doc = DocumentReader.procesar_documento(ruta)

                if not doc['valido']:
                    logger.warning(f"⚠️  Documento inválido: {archivo_info['nombre_guardado']}")
                    continue

                # Clasificar con IA
                contexto = f"Archivo: {archivo_info['nombre_original']}, Email: {archivo_info.get('email_subject', '')}"

                clasificacion = self.classifier.clasificar_documento(
                    doc['imagenes'],
                    doc['texto_extraido'],
                    contexto
                )

                if not clasificacion:
                    logger.warning(f"⚠️  No se pudo clasificar: {archivo_info['nombre_guardado']}")
                    continue

                # Crear transacción
                transaccion = {
                    **clasificacion,
                    "origen": archivo_info['tipo'],
                    "archivo_origen": archivo_info['nombre_original'],
                    "ruta_archivo": ruta,
                    "email_id": archivo_info.get('email_id'),
                    "email_subject": archivo_info.get('email_subject'),
                    "email_from": archivo_info.get('email_from'),
                    "procesado_por_ia": True
                }

                transacciones.append(transaccion)

                # Registrar archivo procesado
                with self.db.get_session() as session:
                    registrar_archivo_procesado(
                        session,
                        archivo_info['nombre_guardado'],
                        file_hash,
                        archivo_info['tipo'],
                        1,
                        archivo_info.get('email_id')
                    )

                # Mover archivo a carpeta correspondiente
                self.downloader.mover_archivo_procesado(ruta, clasificacion['tipo'])

                logger.info(f"✓ Procesado con IA: {archivo_info['nombre_guardado']} -> {clasificacion['tipo']}/{clasificacion['categoria']}")

            except Exception as e:
                logger.error(f"Error al procesar archivo {archivo_info.get('nombre_guardado')}: {e}")
                continue

        return transacciones

    def procesar_csv(self, archivos):
        """Procesa archivos CSV"""
        transacciones_totales = []

        for archivo_info in archivos:
            try:
                ruta = archivo_info['ruta']
                file_hash = archivo_info['hash']

                # Verificar si ya fue procesado
                with self.db.get_session() as session:
                    if archivo_ya_procesado(session, file_hash):
                        logger.info(f"⏭️  CSV ya procesado: {archivo_info['nombre_guardado']}")
                        continue

                # Leer CSV
                transacciones = self.csv_reader.procesar_csv(ruta)

                if not transacciones:
                    logger.warning(f"⚠️  CSV sin transacciones válidas: {archivo_info['nombre_guardado']}")
                    continue

                # Transformar y categorizar
                transacciones = self.transformer.transformar_batch(transacciones)

                # Agregar metadata
                for t in transacciones:
                    t['archivo_origen'] = archivo_info['nombre_original']
                    t['ruta_archivo'] = ruta
                    t['email_id'] = archivo_info.get('email_id')
                    t['email_subject'] = archivo_info.get('email_subject')
                    t['email_from'] = archivo_info.get('email_from')
                    t['procesado_por_ia'] = False

                transacciones_totales.extend(transacciones)

                # Registrar archivo procesado
                with self.db.get_session() as session:
                    registrar_archivo_procesado(
                        session,
                        archivo_info['nombre_guardado'],
                        file_hash,
                        'csv',
                        len(transacciones),
                        archivo_info.get('email_id')
                    )

                logger.info(f"✓ CSV procesado: {archivo_info['nombre_guardado']} -> {len(transacciones)} transacciones")

            except Exception as e:
                logger.error(f"Error al procesar CSV {archivo_info.get('nombre_guardado')}: {e}")
                continue

        return transacciones_totales

    def guardar_transacciones(self, transacciones):
        """Guarda transacciones en la base de datos"""
        if not transacciones:
            return

        try:
            with self.db.get_session() as session:
                cantidad = crear_transacciones_batch(session, transacciones)
                logger.info(f"💾 {cantidad} transacciones guardadas en BD")

        except Exception as e:
            logger.error(f"❌ Error al guardar transacciones: {e}")

    def procesar_archivos_pendientes(self):
        """Procesa archivos que quedaron pendientes en ciclos anteriores"""
        logger.info("🔄 Verificando archivos pendientes...")

        pendientes = self.downloader.obtener_archivos_pendientes()

        total = sum(len(v) for v in pendientes.values())

        if total == 0:
            logger.info("No hay archivos pendientes")
            return

        logger.info(f"📂 {total} archivos pendientes encontrados")

        # Convertir rutas a formato de archivo_info
        archivos_info = []

        for ruta in pendientes['pdf'] + pendientes['imagenes']:
            archivo_path = Path(ruta)
            with open(ruta, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            tipo = 'pdf' if ruta in pendientes['pdf'] else 'imagen'

            archivos_info.append({
                'ruta': ruta,
                'nombre_guardado': archivo_path.name,
                'nombre_original': archivo_path.name,
                'tipo': tipo,
                'hash': file_hash
            })

        for ruta in pendientes['csv']:
            archivo_path = Path(ruta)
            with open(ruta, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            archivos_info.append({
                'ruta': ruta,
                'nombre_guardado': archivo_path.name,
                'nombre_original': archivo_path.name,
                'tipo': 'csv',
                'hash': file_hash
            })

        # Procesar
        transacciones = self.procesar_archivos(archivos_info)
        self.guardar_transacciones(transacciones)

    def iniciar_monitoreo(self):
        """Inicia el monitoreo continuo de emails"""
        logger.info(f"👀 Monitoreo iniciado - Revisando cada {EMAIL_CHECK_INTERVAL} minutos")

        # Procesar archivos pendientes al inicio
        self.procesar_archivos_pendientes()

        # Ejecutar primer ciclo inmediatamente
        self.ciclo_completo()

        # Programar ciclos periódicos
        schedule.every(EMAIL_CHECK_INTERVAL).minutes.do(self.ciclo_completo)

        # Loop infinito
        while True:
            schedule.run_pending()
            time.sleep(30)  # Revisar cada 30 segundos si hay tareas pendientes


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("💰 FacturIA 2.0 - Sistema de Gestión Financiera Automatizado")
    print("="*60 + "\n")

    try:
        # Crear orquestador
        orchestrator = FacturiaOrchestrator()

        # Modo de operación
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            # Ejecutar solo una vez (modo prueba)
            logger.info("🔧 Modo: Ejecución única")
            orchestrator.procesar_archivos_pendientes()
            orchestrator.ciclo_completo()
        else:
            # Monitoreo continuo
            logger.info("♾️  Modo: Monitoreo continuo")
            orchestrator.iniciar_monitoreo()

    except KeyboardInterrupt:
        logger.info("\n\n⏸️  Sistema detenido por el usuario")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
