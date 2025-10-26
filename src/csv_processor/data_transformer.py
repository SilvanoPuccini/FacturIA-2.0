"""
Transformador de datos CSV
Categoriza transacciones usando reglas y palabras clave
"""
from typing import Dict, List, Optional
from loguru import logger
import re


class DataTransformer:
    """Transforma y categoriza datos de transacciones CSV"""

    def __init__(self, categorias_ingresos: List[str], categorias_egresos: List[str]):
        """
        Inicializa el transformador

        Args:
            categorias_ingresos: Lista de categorías válidas para ingresos
            categorias_egresos: Lista de categorías válidas para egresos
        """
        self.categorias_ingresos = categorias_ingresos
        self.categorias_egresos = categorias_egresos

        # Reglas de categorización por palabras clave
        self.reglas_ingresos = {
            "sueldo": ["sueldo", "salario", "salary", "payroll", "remuneracion", "haberes"],
            "cobro_servicios": ["cobro", "pago recibido", "factura cobrada", "payment received"],
            "deposito": ["deposito", "deposit", "transferencia recibida", "ingreso"],
            "ventas": ["venta", "sale", "ingreso por venta", "revenue"],
            "transferencia_recibida": ["transferencia", "transfer", "enviado por"],
        }

        self.reglas_egresos = {
            "factura_servicios": [
                "edenor", "edesur", "metrogas", "telecom", "fibertel", "personal", "movistar",
                "luz", "agua", "gas", "internet", "telefono", "electricity", "water", "internet"
            ],
            "supermercado": [
                "carrefour", "coto", "dia", "walmart", "jumbo", "disco", "supermercado",
                "supermarket", "mercado", "grocery"
            ],
            "impuestos": [
                "afip", "arba", "impuesto", "tax", "contribucion", "tributo", "municipal"
            ],
            "alquiler": ["alquiler", "rent", "rental", "arriendo"],
            "combustible": ["ypf", "shell", "axion", "combustible", "fuel", "gas station", "nafta", "gasoil"],
            "salud": [
                "osde", "swiss medical", "farmacia", "hospital", "clinica", "medico",
                "pharmacy", "health", "medicina", "consulta"
            ],
            "entretenimiento": [
                "netflix", "spotify", "cine", "teatro", "restaurant", "entretenimiento",
                "entertainment", "streaming", "disney", "hbo"
            ],
        }

    def categorizar_transaccion(self, transaccion: Dict) -> Dict:
        """
        Categoriza una transacción basándose en su descripción y tipo

        Args:
            transaccion: Diccionario con datos de la transacción

        Returns:
            Transacción con categoría asignada
        """
        # Si ya tiene categoría válida, no hacer nada
        if self._validar_categoria(transaccion):
            return transaccion

        tipo = transaccion.get("tipo")
        descripcion = transaccion.get("descripcion", "").lower()
        emisor_receptor = transaccion.get("emisor_receptor", "").lower()

        # Combinar descripción y emisor para análisis
        texto_completo = f"{descripcion} {emisor_receptor}"

        if tipo == "ingreso":
            categoria = self._buscar_categoria(texto_completo, self.reglas_ingresos)
            transaccion["categoria"] = categoria if categoria else "otro_ingreso"

        elif tipo == "egreso":
            categoria = self._buscar_categoria(texto_completo, self.reglas_egresos)
            transaccion["categoria"] = categoria if categoria else "otro_egreso"

        else:
            logger.warning(f"Tipo de transacción inválido: {tipo}")
            transaccion["categoria"] = None

        logger.debug(f"Categorizada: {tipo} -> {transaccion['categoria']}")

        return transaccion

    def _buscar_categoria(self, texto: str, reglas: Dict[str, List[str]]) -> Optional[str]:
        """
        Busca una categoría que coincida con las palabras clave

        Args:
            texto: Texto a analizar
            reglas: Diccionario de categoría -> palabras clave

        Returns:
            Categoría encontrada o None
        """
        for categoria, palabras_clave in reglas.items():
            for palabra in palabras_clave:
                # Usar regex para buscar palabra completa (con word boundaries)
                patron = r'\b' + re.escape(palabra.lower()) + r'\b'

                if re.search(patron, texto):
                    logger.debug(f"Match: '{palabra}' -> {categoria}")
                    return categoria

        return None

    def _validar_categoria(self, transaccion: Dict) -> bool:
        """
        Valida si la transacción ya tiene una categoría válida

        Args:
            transaccion: Diccionario con datos de la transacción

        Returns:
            True si tiene categoría válida
        """
        categoria = transaccion.get("categoria")
        tipo = transaccion.get("tipo")

        if not categoria:
            return False

        if tipo == "ingreso":
            return categoria in self.categorias_ingresos
        elif tipo == "egreso":
            return categoria in self.categorias_egresos
        else:
            return False

    def categorizar_lote(self, transacciones: List[Dict]) -> List[Dict]:
        """
        Categoriza un lote de transacciones

        Args:
            transacciones: Lista de transacciones

        Returns:
            Lista de transacciones categorizadas
        """
        logger.info(f"📊 Categorizando {len(transacciones)} transacciones...")

        transacciones_categorizadas = []

        for transaccion in transacciones:
            transaccion_categorizada = self.categorizar_transaccion(transaccion)
            transacciones_categorizadas.append(transaccion_categorizada)

        # Estadísticas
        sin_categoria = sum(
            1 for t in transacciones_categorizadas
            if t.get("categoria") in ["otro_ingreso", "otro_egreso", None]
        )

        logger.info(f"✅ Categorizadas: {len(transacciones_categorizadas)}")
        logger.info(f"   Sin categoría específica: {sin_categoria}")

        return transacciones_categorizadas

    def limpiar_transaccion(self, transaccion: Dict) -> Dict:
        """
        Limpia y normaliza los datos de una transacción

        Args:
            transaccion: Diccionario con datos de la transacción

        Returns:
            Transacción limpia
        """
        # Limpiar strings
        if transaccion.get("descripcion"):
            transaccion["descripcion"] = transaccion["descripcion"].strip()

        if transaccion.get("emisor_receptor"):
            transaccion["emisor_receptor"] = transaccion["emisor_receptor"].strip()

        # Normalizar monto (asegurar que sea positivo)
        if transaccion.get("monto"):
            transaccion["monto"] = abs(float(transaccion["monto"]))

        # Asegurar que tenga fecha (usar hoy si no tiene)
        if not transaccion.get("fecha"):
            from datetime import datetime
            transaccion["fecha"] = datetime.now().strftime('%Y-%m-%d')

        return transaccion

    def transformar_batch(self, transacciones: List[Dict]) -> List[Dict]:
        """
        Transforma un lote completo de transacciones

        Args:
            transacciones: Lista de transacciones

        Returns:
            Lista de transacciones transformadas y listas para BD
        """
        logger.info(f"🔄 Transformando {len(transacciones)} transacciones...")

        transacciones_transformadas = []

        for transaccion in transacciones:
            # Limpiar
            transaccion = self.limpiar_transaccion(transaccion)

            # Categorizar
            transaccion = self.categorizar_transaccion(transaccion)

            transacciones_transformadas.append(transaccion)

        logger.info(f"✅ Transformación completada")

        return transacciones_transformadas

    def agrupar_por_categoria(self, transacciones: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa transacciones por categoría

        Args:
            transacciones: Lista de transacciones

        Returns:
            Diccionario de categoría -> lista de transacciones
        """
        grupos = {}

        for transaccion in transacciones:
            categoria = transaccion.get("categoria", "sin_categoria")

            if categoria not in grupos:
                grupos[categoria] = []

            grupos[categoria].append(transaccion)

        return grupos

    def calcular_estadisticas(self, transacciones: List[Dict]) -> Dict:
        """
        Calcula estadísticas de las transacciones

        Args:
            transacciones: Lista de transacciones

        Returns:
            Diccionario con estadísticas
        """
        if not transacciones:
            return {
                "total_transacciones": 0,
                "total_ingresos": 0,
                "total_egresos": 0,
                "cantidad_ingresos": 0,
                "cantidad_egresos": 0
            }

        ingresos = [t for t in transacciones if t.get("tipo") == "ingreso"]
        egresos = [t for t in transacciones if t.get("tipo") == "egreso"]

        total_ingresos = sum(t.get("monto", 0) for t in ingresos)
        total_egresos = sum(t.get("monto", 0) for t in egresos)

        return {
            "total_transacciones": len(transacciones),
            "total_ingresos": round(total_ingresos, 2),
            "total_egresos": round(total_egresos, 2),
            "cantidad_ingresos": len(ingresos),
            "cantidad_egresos": len(egresos),
            "balance": round(total_ingresos - total_egresos, 2)
        }


if __name__ == "__main__":
    # Prueba del módulo
    from src.config import CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS

    transformer = DataTransformer(CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS)

    # Transacciones de prueba
    transacciones_test = [
        {
            "tipo": "egreso",
            "monto": 15000.50,
            "descripcion": "Factura Edenor Octubre 2024",
            "emisor_receptor": "Edenor SA",
            "fecha": "2024-10-15"
        },
        {
            "tipo": "ingreso",
            "monto": 500000,
            "descripcion": "Sueldo Octubre",
            "emisor_receptor": "Empresa XYZ",
            "fecha": "2024-10-01"
        },
        {
            "tipo": "egreso",
            "monto": 35000,
            "descripcion": "Compras Carrefour",
            "emisor_receptor": "Carrefour",
            "fecha": "2024-10-10"
        }
    ]

    print("\n🔄 Transformando transacciones...\n")

    transacciones_transformadas = transformer.transformar_batch(transacciones_test)

    for t in transacciones_transformadas:
        print(f"{t['tipo'].upper()}: ${t['monto']:.2f}")
        print(f"   Categoría: {t['categoria']}")
        print(f"   Descripción: {t['descripcion']}")
        print()

    # Estadísticas
    stats = transformer.calcular_estadisticas(transacciones_transformadas)
    print("\n📊 Estadísticas:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
