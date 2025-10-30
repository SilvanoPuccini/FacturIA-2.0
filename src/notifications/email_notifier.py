"""
Sistema de Notificaciones por Email para FacturIA 2.1.0
Envía alertas cuando se procesan transacciones
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import os


class EmailNotifier:
    """Notificador de eventos por email"""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        email_from: str = None,
        email_password: str = None,
        email_to: List[str] = None
    ):
        """
        Inicializa el notificador de email

        Args:
            smtp_server: Servidor SMTP (default: Gmail)
            smtp_port: Puerto SMTP (default: 587)
            email_from: Email remitente
            email_password: Contraseña del remitente (App Password para Gmail)
            email_to: Lista de emails destinatarios
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_from = email_from
        self.email_password = email_password
        self.email_to = email_to or []

        # Validar configuración
        if not self.email_from or not self.email_password:
            logger.warning("⚠️ Email notifier no configurado completamente")
            self.habilitado = False
        else:
            self.habilitado = True
            logger.info(f"✅ Email notifier configurado: {self.email_from}")

    def enviar_notificacion_procesamiento(
        self,
        transacciones: List[Dict],
        exitosas: int,
        fallidas: int,
        archivos_procesados: List[str] = None
    ) -> bool:
        """
        Envía notificación sobre transacciones procesadas

        Args:
            transacciones: Lista de transacciones procesadas
            exitosas: Cantidad exitosa
            fallidas: Cantidad fallida
            archivos_procesados: Lista de nombres de archivos

        Returns:
            True si se envió correctamente
        """
        if not self.habilitado:
            logger.warning("Email notifier deshabilitado - no se envía notificación")
            return False

        try:
            # Calcular estadísticas
            total_ingresos = sum(t.get('monto', 0) for t in transacciones if t.get('tipo') == 'ingreso')
            total_egresos = sum(t.get('monto', 0) for t in transacciones if t.get('tipo') == 'egreso')
            balance = total_ingresos - total_egresos

            # Crear mensaje HTML
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            color: #333;
                            line-height: 1.6;
                        }}
                        .header {{
                            background-color: #00CC66;
                            color: white;
                            padding: 20px;
                            text-align: center;
                        }}
                        .content {{
                            padding: 20px;
                        }}
                        .stats-box {{
                            background-color: #f4f4f4;
                            border-left: 4px solid #00CC66;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                        .success {{
                            color: #00CC66;
                            font-weight: bold;
                        }}
                        .error {{
                            color: #FF4444;
                            font-weight: bold;
                        }}
                        .transaction {{
                            border-bottom: 1px solid #ddd;
                            padding: 10px 0;
                        }}
                        .footer {{
                            text-align: center;
                            padding: 20px;
                            font-size: 12px;
                            color: #666;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>💰 FacturIA 2.1.0 - Notificación de Procesamiento</h1>
                    </div>

                    <div class="content">
                        <p>Se han procesado nuevas transacciones:</p>

                        <div class="stats-box">
                            <h3>📊 Resumen del Procesamiento</h3>
                            <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>Total procesadas:</strong> {exitosas + fallidas}</p>
                            <p><span class="success">✅ Exitosas: {exitosas}</span></p>
                            {f'<p><span class="error">❌ Fallidas: {fallidas}</span></p>' if fallidas > 0 else ''}
                        </div>

                        <div class="stats-box">
                            <h3>💵 Estadísticas Financieras</h3>
                            <p><strong>Total Ingresos:</strong> ${total_ingresos:,.2f}</p>
                            <p><strong>Total Egresos:</strong> ${total_egresos:,.2f}</p>
                            <p><strong>Balance:</strong> <span style="color: {'#00CC66' if balance > 0 else '#FF4444'};">${balance:,.2f}</span></p>
                        </div>

                        {self._generar_lista_archivos(archivos_procesados) if archivos_procesados else ''}

                        {self._generar_lista_transacciones(transacciones[:10])}

                        <p style="margin-top: 20px;">
                            <a href="http://localhost:8501" style="background-color: #00CC66; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                                Ver Dashboard
                            </a>
                        </p>
                    </div>

                    <div class="footer">
                        <p>Este es un mensaje automático de <strong>FacturIA 2.1.0</strong></p>
                        <p>Sistema de Gestión Financiera Automatizado con IA</p>
                    </div>
                </body>
            </html>
            """

            # Enviar email
            asunto = f"💰 FacturIA: {exitosas} transacciones procesadas"

            return self._enviar_email(asunto, html_body, html=True)

        except Exception as e:
            logger.error(f"❌ Error al enviar notificación por email: {e}")
            return False

    def enviar_alerta_error(self, error_msg: str, detalle: str = None) -> bool:
        """
        Envía alerta de error crítico

        Args:
            error_msg: Mensaje de error
            detalle: Detalle adicional

        Returns:
            True si se envió correctamente
        """
        if not self.habilitado:
            return False

        try:
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        .header {{ background-color: #FF4444; color: white; padding: 20px; text-align: center; }}
                        .content {{ padding: 20px; }}
                        .error-box {{ background-color: #ffebee; border-left: 4px solid #FF4444; padding: 15px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>⚠️ FacturIA - Alerta de Error</h1>
                    </div>
                    <div class="content">
                        <div class="error-box">
                            <h3>Error Detectado</h3>
                            <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>Mensaje:</strong> {error_msg}</p>
                            {f'<p><strong>Detalle:</strong> {detalle}</p>' if detalle else ''}
                        </div>
                        <p>Se recomienda revisar el sistema lo antes posible.</p>
                    </div>
                </body>
            </html>
            """

            asunto = "⚠️ FacturIA: Error Crítico Detectado"

            return self._enviar_email(asunto, html_body, html=True)

        except Exception as e:
            logger.error(f"❌ Error al enviar alerta de error: {e}")
            return False

    def _generar_lista_archivos(self, archivos: List[str]) -> str:
        """Genera HTML con lista de archivos procesados"""
        html = '<div class="stats-box"><h3>📁 Archivos Procesados</h3><ul>'
        for archivo in archivos[:20]:  # Máximo 20
            html += f'<li>{archivo}</li>'
        html += '</ul></div>'
        return html

    def _generar_lista_transacciones(self, transacciones: List[Dict]) -> str:
        """Genera HTML con lista de transacciones"""
        if not transacciones:
            return ""

        html = '<div class="stats-box"><h3>📋 Últimas Transacciones</h3>'

        for t in transacciones:
            tipo_icon = "💵" if t.get('tipo') == 'ingreso' else "💸"
            html += f"""
            <div class="transaction">
                <p>
                    {tipo_icon} <strong>{t.get('categoria', 'N/A')}</strong> - ${t.get('monto', 0):,.2f}<br>
                    <small>{t.get('descripcion', 'Sin descripción')}</small>
                </p>
            </div>
            """

        html += '</div>'
        return html

    def _enviar_email(self, asunto: str, cuerpo: str, html: bool = False) -> bool:
        """
        Envía un email

        Args:
            asunto: Asunto del email
            cuerpo: Cuerpo del email
            html: Si es HTML o texto plano

        Returns:
            True si se envió correctamente
        """
        try:
            # Crear mensaje
            mensaje = MIMEMultipart()
            mensaje['From'] = self.email_from
            mensaje['To'] = ', '.join(self.email_to)
            mensaje['Subject'] = asunto

            # Adjuntar cuerpo
            if html:
                mensaje.attach(MIMEText(cuerpo, 'html'))
            else:
                mensaje.attach(MIMEText(cuerpo, 'plain'))

            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(mensaje)

            logger.info(f"✅ Email enviado a {', '.join(self.email_to)}")
            return True

        except Exception as e:
            logger.error(f"❌ Error al enviar email: {e}")
            return False

    def test_conexion(self) -> bool:
        """
        Prueba la conexión SMTP

        Returns:
            True si la conexión es exitosa
        """
        if not self.habilitado:
            logger.warning("Email notifier no configurado")
            return False

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)

            logger.info("✅ Conexión SMTP exitosa")
            return True

        except Exception as e:
            logger.error(f"❌ Error de conexión SMTP: {e}")
            return False


# Función helper para crear notifier desde config
def crear_notifier_desde_env() -> EmailNotifier:
    """
    Crea un notifier usando variables de entorno

    Variables requeridas:
    - NOTIFICATION_EMAIL_FROM: Email remitente
    - NOTIFICATION_EMAIL_PASSWORD: Contraseña (App Password)
    - NOTIFICATION_EMAIL_TO: Emails destinatarios (separados por coma)

    Returns:
        EmailNotifier configurado
    """
    email_from = os.getenv("NOTIFICATION_EMAIL_FROM")
    email_password = os.getenv("NOTIFICATION_EMAIL_PASSWORD")
    email_to_str = os.getenv("NOTIFICATION_EMAIL_TO", "")

    email_to = [e.strip() for e in email_to_str.split(",") if e.strip()]

    return EmailNotifier(
        email_from=email_from,
        email_password=email_password,
        email_to=email_to
    )


if __name__ == "__main__":
    # Prueba del módulo
    print("\n🔔 EmailNotifier - Módulo de Notificaciones\n")

    notifier = crear_notifier_desde_env()

    if notifier.habilitado:
        print("✅ Notifier configurado")
        print(f"   Email: {notifier.email_from}")
        print(f"   Destinatarios: {', '.join(notifier.email_to)}")

        # Probar conexión
        if notifier.test_conexion():
            print("\n✅ Conexión SMTP exitosa")
        else:
            print("\n❌ Error en conexión SMTP")
    else:
        print("⚠️ Notifier no configurado")
        print("\nPara configurar, agrega al .env:")
        print("  NOTIFICATION_EMAIL_FROM=tu_email@gmail.com")
        print("  NOTIFICATION_EMAIL_PASSWORD=tu_app_password")
        print("  NOTIFICATION_EMAIL_TO=destinatario@email.com")
