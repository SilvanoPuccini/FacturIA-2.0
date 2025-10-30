"""
Módulo de Notificaciones - FacturIA 2.1.0
"""
from .email_notifier import EmailNotifier, crear_notifier_desde_env

__all__ = ['EmailNotifier', 'crear_notifier_desde_env']
