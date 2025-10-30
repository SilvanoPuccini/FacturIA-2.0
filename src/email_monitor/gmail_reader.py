"""
Monitor de emails Gmail usando IMAP
Lee emails no leídos y detecta adjuntos financieros
"""
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import sys
import time
import socket

# Configurar logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/email_monitor.log", rotation="10 MB", level="DEBUG")


class GmailReader:
    """Cliente IMAP para leer emails de Gmail"""

    def __init__(self, email_address: str, password: str, timeout: int = 30, max_reintentos: int = 3):
        """
        Inicializa el lector de Gmail

        Args:
            email_address: Email de Gmail
            password: App Password de Gmail (no la contraseña normal)
            timeout: Timeout para conexiones IMAP en segundos (default: 30)
            max_reintentos: Número máximo de reintentos en caso de fallo (default: 3)
        """
        self.email_address = email_address
        self.password = password
        self.timeout = timeout
        self.max_reintentos = max_reintentos
        self.imap = None
        self.connected = False

    def conectar(self) -> bool:
        """
        Conecta al servidor IMAP de Gmail con reintentos y backoff exponencial

        Returns:
            True si la conexión fue exitosa
        """
        for intento in range(1, self.max_reintentos + 1):
            try:
                logger.info(f"Conectando a Gmail con {self.email_address}... (intento {intento}/{self.max_reintentos})")

                # Establecer timeout para socket
                socket.setdefaulttimeout(self.timeout)

                # Conectar con timeout
                self.imap = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=self.timeout)
                self.imap.login(self.email_address, self.password)
                self.connected = True
                logger.info("✅ Conectado exitosamente a Gmail")
                return True

            except imaplib.IMAP4.error as e:
                logger.error(f"❌ Error de autenticación IMAP: {e}")
                logger.error("💡 Verifica que uses un App Password, no tu contraseña normal")
                # No reintentar en errores de autenticación
                return False

            except (socket.timeout, TimeoutError) as e:
                logger.warning(f"⏱️ Timeout al conectar a Gmail (intento {intento}/{self.max_reintentos}): {e}")
                if intento < self.max_reintentos:
                    wait_time = 2 ** intento  # Backoff exponencial: 2, 4, 8 segundos
                    logger.info(f"⏳ Esperando {wait_time}s antes del siguiente intento...")
                    time.sleep(wait_time)
                else:
                    logger.error("❌ Máximo de reintentos alcanzado para conexión IMAP")
                    return False

            except (socket.error, ConnectionError, OSError) as e:
                logger.warning(f"🌐 Error de red al conectar (intento {intento}/{self.max_reintentos}): {e}")
                if intento < self.max_reintentos:
                    wait_time = 2 ** intento  # Backoff exponencial
                    logger.info(f"⏳ Esperando {wait_time}s antes del siguiente intento...")
                    time.sleep(wait_time)
                else:
                    logger.error("❌ Máximo de reintentos alcanzado - error de red persistente")
                    return False

            except Exception as e:
                logger.error(f"❌ Error inesperado al conectar a Gmail: {type(e).__name__}: {e}")
                if intento < self.max_reintentos:
                    wait_time = 2 ** intento
                    logger.info(f"⏳ Esperando {wait_time}s antes del siguiente intento...")
                    time.sleep(wait_time)
                else:
                    return False

        return False

    def desconectar(self):
        """Cierra la conexión IMAP"""
        if self.imap and self.connected:
            try:
                self.imap.close()
                self.imap.logout()
                self.connected = False
                logger.info("✅ Desconectado de Gmail")
            except Exception as e:
                logger.warning(f"⚠️ Error al desconectar (no crítico): {type(e).__name__}: {e}")
                self.connected = False

    def _verificar_y_reconectar(self) -> bool:
        """
        Verifica si la conexión sigue activa y reconecta si es necesario

        Returns:
            True si hay conexión activa (existente o recién establecida)
        """
        if not self.connected:
            logger.info("🔄 Conexión no activa, intentando conectar...")
            return self.conectar()

        # Intentar hacer un NOOP para verificar que la conexión sigue viva
        try:
            status = self.imap.noop()
            if status[0] == 'OK':
                return True
        except Exception as e:
            logger.warning(f"⚠️ Conexión perdida: {e}")
            self.connected = False

        # Si llegamos aquí, la conexión está muerta, intentar reconectar
        logger.info("🔄 Reconectando a Gmail...")
        return self.conectar()

    def obtener_emails_no_leidos(self, carpeta: str = "INBOX", reintentos: int = 2) -> List[Dict]:
        """
        Obtiene todos los emails no leídos con adjuntos

        Args:
            carpeta: Carpeta de Gmail a revisar (default: INBOX)
            reintentos: Número de reintentos en caso de error (default: 2)

        Returns:
            Lista de diccionarios con información de emails
        """
        for intento in range(1, reintentos + 1):
            # Verificar y reconectar si es necesario
            if not self._verificar_y_reconectar():
                logger.error("❌ No se pudo establecer conexión con Gmail")
                if intento < reintentos:
                    wait_time = 2 ** intento
                    logger.info(f"⏳ Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                    continue
                return []

            try:
                # Seleccionar carpeta
                self.imap.select(carpeta)

                # Buscar emails no leídos
                status, messages = self.imap.search(None, "UNSEEN")

                if status != "OK":
                    logger.error(f"Error al buscar emails: {status}")
                    if intento < reintentos:
                        wait_time = 2 ** intento
                        time.sleep(wait_time)
                        continue
                    return []

                email_ids = messages[0].split()

                if not email_ids:
                    logger.info("No hay emails no leídos")
                    return []

                logger.info(f"📬 Encontrados {len(email_ids)} emails no leídos")

                emails_con_adjuntos = []

                for email_id in email_ids:
                    email_data = self._procesar_email(email_id)
                    if email_data and email_data.get("adjuntos"):
                        emails_con_adjuntos.append(email_data)

                logger.info(f"✅ {len(emails_con_adjuntos)} emails con adjuntos válidos")
                return emails_con_adjuntos

            except (socket.timeout, TimeoutError) as e:
                logger.warning(f"⏱️ Timeout al obtener emails (intento {intento}/{reintentos}): {e}")
                self.connected = False
                if intento < reintentos:
                    wait_time = 2 ** intento
                    logger.info(f"⏳ Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                else:
                    return []

            except (socket.error, ConnectionError, imaplib.IMAP4.abort) as e:
                logger.warning(f"🌐 Error de conexión al obtener emails (intento {intento}/{reintentos}): {e}")
                self.connected = False
                if intento < reintentos:
                    wait_time = 2 ** intento
                    logger.info(f"⏳ Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                else:
                    return []

            except Exception as e:
                logger.error(f"❌ Error inesperado al obtener emails: {type(e).__name__}: {e}")
                if intento < reintentos:
                    wait_time = 2 ** intento
                    time.sleep(wait_time)
                else:
                    return []

        return []

    def _procesar_email(self, email_id: bytes) -> Optional[Dict]:
        """
        Procesa un email individual y extrae su información

        Args:
            email_id: ID del email en el servidor

        Returns:
            Diccionario con datos del email o None si no es válido
        """
        try:
            # Obtener el email completo
            status, msg_data = self.imap.fetch(email_id, "(RFC822)")

            if status != "OK":
                return None

            # Parsear el email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extraer información básica
            subject = self._decode_subject(msg.get("Subject", "Sin asunto"))
            from_raw = msg.get("From", "Desconocido")
            from_ = self._extraer_email_puro(from_raw)  # Extraer solo el email limpio
            date_str = msg.get("Date", "")

            # Procesar adjuntos
            adjuntos = []

            if msg.is_multipart():
                for part in msg.walk():
                    adjuntos.extend(self._extraer_adjuntos_parte(part))
            else:
                adjuntos.extend(self._extraer_adjuntos_parte(msg))

            # Solo retornar si tiene adjuntos válidos (PDF, PNG, JPG, CSV)
            adjuntos_validos = [
                adj for adj in adjuntos
                if any(adj["filename"].lower().endswith(ext)
                       for ext in [".pdf", ".png", ".jpg", ".jpeg", ".csv"])
            ]

            if not adjuntos_validos:
                return None

            email_data = {
                "id": email_id.decode(),
                "subject": subject,
                "from": from_,
                "date": date_str,
                "adjuntos": adjuntos_validos,
                "fecha_procesamiento": datetime.now().isoformat()
            }

            logger.debug(f"📧 Email procesado: {subject} - {len(adjuntos_validos)} adjuntos")

            return email_data

        except Exception as e:
            logger.error(f"Error al procesar email {email_id}: {e}")
            return None

    def _decode_subject(self, subject: str) -> str:
        """Decodifica el asunto del email"""
        try:
            decoded_parts = decode_header(subject)
            decoded_subject = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    decoded_subject += part

            return decoded_subject
        except Exception as e:
            logger.warning(f"Error al decodificar asunto: {e}")
            return subject

    def _extraer_email_puro(self, from_field: str) -> str:
        """
        Extrae solo el email desde el campo From

        Ejemplos:
            "Silvano Puccini <silva_puccini@hotmail.com>" -> "silva_puccini@hotmail.com"
            "silva.jm.puccini@gmail.com" -> "silva.jm.puccini@gmail.com"
        """
        import re

        # Buscar email entre < >
        match = re.search(r'<([^>]+)>', from_field)
        if match:
            return match.group(1).strip()

        # Si no hay < >, asumir que todo el campo es el email
        # Extraer usando regex simple de email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_field)
        if email_match:
            return email_match.group(0).strip()

        # Si no se puede extraer, devolver el campo completo limpio
        return from_field.strip()

    def _extraer_adjuntos_parte(self, part) -> List[Dict]:
        """
        Extrae adjuntos de una parte del email

        Args:
            part: Parte del mensaje multipart

        Returns:
            Lista de diccionarios con información de adjuntos
        """
        adjuntos = []

        try:
            # Verificar si es un adjunto
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()

                if filename:
                    # Decodificar nombre del archivo
                    decoded_filename = self._decode_subject(filename)

                    adjuntos.append({
                        "filename": decoded_filename,
                        "content": part.get_payload(decode=True),
                        "content_type": part.get_content_type()
                    })

        except Exception as e:
            logger.error(f"Error al extraer adjunto: {e}")

        return adjuntos

    def marcar_como_leido(self, email_id: str):
        """
        Marca un email como leído

        Args:
            email_id: ID del email a marcar
        """
        try:
            self.imap.store(email_id.encode(), "+FLAGS", "\\Seen")
            logger.debug(f"✓ Email {email_id} marcado como leído")
        except Exception as e:
            logger.error(f"Error al marcar email como leído: {e}")

    def __enter__(self):
        """Context manager: conectar automáticamente"""
        self.conectar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: desconectar automáticamente"""
        self.desconectar()


if __name__ == "__main__":
    # Prueba del módulo
    from dotenv import load_dotenv
    import os

    load_dotenv()

    email_addr = os.getenv("GMAIL_EMAIL")
    email_pass = os.getenv("GMAIL_PASSWORD")

    if not email_addr or not email_pass:
        print("❌ Falta configurar GMAIL_EMAIL y GMAIL_PASSWORD en .env")
        exit(1)

    # Usar como context manager
    with GmailReader(email_addr, email_pass) as reader:
        emails = reader.obtener_emails_no_leidos()

        print(f"\n📊 Total de emails con adjuntos: {len(emails)}\n")

        for email_data in emails:
            print(f"📧 Asunto: {email_data['subject']}")
            print(f"   De: {email_data['from']}")
            print(f"   Adjuntos: {len(email_data['adjuntos'])}")
            for adj in email_data['adjuntos']:
                print(f"      - {adj['filename']}")
            print()
