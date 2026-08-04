"""
Avisos de ejemplo para probar el sistema sin depender de la red.

Son avisos REALES: los tres que Marcelo Quinones envio por WhatsApp el 3 de
agosto de 2026. Sirven de prueba de regresion porque cubren los tres casos
interesantes: fuera de zona por localidad trampa, zona valida con reparo de
forma de pago, y fuera de zona con precio atractivo.
"""

AVISOS_EJEMPLO = [
    {
        "id": "wa-maderos-ensenada",
        "fuente": "Instagram (reenviado por WhatsApp)",
        "url": "https://www.instagram.com/p/DZxnBRAAHm9/",
        "titulo": "Hacienda Maderos Ensenada - Parcelas desde 1.600 UF",
        "ubicacion": "Ensenada",
        "precio_texto": "Parcelas desde 1.600 UF",
        "fecha": "2026-08-03",
        "descripcion": (
            "Hay quienes visitan la montana. Y hay quienes viven cerca de ella. "
            "Mientras otros planifican escapadas de fin de semana, en Hacienda Maderos "
            "puedes tener un lugar propio para disfrutar el invierno, la nieve y la "
            "naturaleza. Parcelas desde 1.600 UF. Ensenada. Porque los mejores paisajes "
            "no deberian ser solo para las vacaciones."
        ),
    },
    {
        "id": "wa-chiloe-nativo-coquiao",
        "fuente": "Instagram (reenviado por WhatsApp)",
        "url": "https://www.instagram.com/p/DblgK4NgBuf/",
        "titulo": "Chiloe Nativo - Ultimas 18 parcelas en Coquiao, Ancud",
        "ubicacion": "Coquiao, Ancud, Isla de Chiloe",
        "precio_texto": "Desde $13.000.000 y $14.000.000",
        "fecha": "2026-08-03",
        "descripcion": (
            "Ultimas 18 parcelas disponibles en Coquiao, Ancud - Isla de Chiloe. "
            "Haz realidad tu proyecto de vida o inversion en un entorno natural unico, "
            "ubicado a solo 17 minutos de Ancud. Parcelas de 5.000 m2 con rol propio. "
            "Valores desde $13.000.000 y $14.000.000. Credito directo disponible. "
            "Caminos interiores completamente terminados. Factibilidad de luz electrica "
            "dentro del proyecto. Agua mediante vertientes subterraneas. Parcelas con "
            "praderas y bosque nativo, ideales para disfrutar la tranquilidad y la "
            "naturaleza de Chiloe. Excelente ubicacion, con facil acceso y entrega "
            "inmediata. No dejes pasar esta oportunidad! Las unidades disponibles son "
            "limitadas. Contactanos para conocer la disponibilidad y agendar tu visita. "
            "+56964748283"
        ),
    },
    {
        "id": "wa-portalterreno-sjlc",
        "fuente": "Instagram (reenviado por WhatsApp)",
        "url": "https://www.instagram.com/p/DVOCIOQjBx5/",
        "titulo": "PortalTerreno Chile - Parcelas en San Juan de La Costa",
        "ubicacion": "San Juan de La Costa",
        "precio_texto": "$11.990.000",
        "fecha": "2026-08-03",
        "descripcion": (
            "Parcelas en venta en San Juan de La Costa, desde 5.000 m2 a $11.990.000. "
            "Haz click en el boton cotizar para recibir informacion del proyecto. "
            "#terrenos #parcelas #chile"
        ),
    },
]
