"""
Semilla del historico: los tres avisos que Marcelo Quinones envio por WhatsApp
el 3 de agosto de 2026, ya evaluados con los criterios del Proyecto.

Sirve para que la web y el primer correo no salgan vacios, y como caso de
referencia para comparar precios futuros en Chiloe.

Correr una sola vez:  python semilla.py
"""

import almacen

FICHAS = [
    {
        "id": "wa-chiloe-nativo-coquiao",
        "url": "https://www.instagram.com/p/DblgK4NgBuf/",
        "fuente": "Instagram - Chiloe Nativo (reenviado por Marcelo)",
        "titulo": "Chiloe Nativo - Ultimas 18 parcelas en Coquiao, Ancud",
        "ubicacion_comuna": "Coquiao, Ancud",
        "zona": "Isla de Chiloe",
        "superficie": "5.000 m2",
        "precio_clp": 13000000,
        "precio_texto": "Desde $13.000.000, con unidades a $14.000.000",
        "forma_pago": "El aviso solo ofrece credito directo; no publica precio al contado",
        "cumple_contado": None,
        "estado_rol": "El aviso declara rol propio - falta verificarlo en el SII",
        "agua": "Vertientes subterraneas. No menciona derecho de aprovechamiento constituido en la DGA",
        "agua_ok": None,
        "luz": "Factibilidad electrica dentro del proyecto (factibilidad, no empalme ejecutado)",
        "luz_ok": True,
        "fecha_publicacion": "2026-08-03 (fecha de reenvio)",
        "veredicto": "Cumple con reservas",
        "puntaje": 3,
        "justificacion_puntaje": (
            "Esta en zona valida y a 17 minutos de Ancud, que es la mejor variable del aviso: "
            "acceso real a servicios y a la ruta 5. Tiene rol propio declarado, caminos "
            "interiores terminados y factibilidad electrica, que es mas de lo que ofrece el "
            "loteo promedio. Pero el precio parte en el techo tolerable de $13-14 millones, no "
            "en el objetivo de $10 millones, y el agua depende de vertientes sin derecho "
            "constituido. Con un descuento por pago al contado y el derecho de agua saneado "
            "subiria a 4; tal como esta publicado, es un 3."
        ),
        "riesgos": [
            "El agua es por 'vertientes subterraneas': eso no es un derecho de aprovechamiento "
            "constituido en la DGA. Sin ese derecho inscrito, el suministro no esta garantizado "
            "juridicamente y el costo de un pozo queda en tu cancha.",
            "El aviso promociona credito directo, no venta al contado. El criterio del proyecto "
            "es contado: hay que negociar precio de contado, que deberia ser bastante menor a "
            "$13 millones.",
            "18 parcelas de 5.000 m2 son unas 9 hectareas subdivididas: hay que revisar que la "
            "subdivision este autorizada y con planos aprobados, no solo que exista un rol.",
            "$13-14 millones esta en el limite superior del rango aceptable y no hay avisos "
            "previos en Chiloe en este historico con que compararlo.",
        ],
        "datos_faltantes": [
            "Cual es el precio al contado y que descuento hay respecto del credito directo",
            "Numero de rol de una parcela concreta, para verificarlo en el SII",
            "Existe derecho de aprovechamiento de aguas constituido en la DGA, o solo vertiente de hecho",
            "Copia del plano de subdivision aprobado y del certificado del SAG",
            "Que significa exactamente 'factibilidad electrica': hay poste en el deslinde o hay que costear la extension",
            "Nombre y RUT de la sociedad vendedora, para revisar el estudio de titulos",
        ],
        "comparacion_zona": "Primer aviso registrado en Isla de Chiloe: queda como precio de referencia inicial.",
        "primera_vez": "2026-08-03T19:40:00",
        "visto_ultima_vez": "2026-08-03T19:40:00",
        "veces_visto": 1,
        "_error": None,
    },
    {
        "id": "wa-maderos-ensenada",
        "url": "https://www.instagram.com/p/DZxnBRAAHm9/",
        "fuente": "Instagram - Hacienda Maderos (reenviado por Marcelo)",
        "titulo": "Hacienda Maderos Ensenada - Parcelas desde 1.600 UF",
        "ubicacion_comuna": "Ensenada, comuna de Puerto Varas",
        "zona": "Fuera de zona",
        "superficie": "dato faltante",
        "precio_clp": 64800000,
        "precio_texto": "Desde 1.600 UF (aprox. $64.800.000 con UF de referencia)",
        "forma_pago": "dato faltante",
        "cumple_contado": None,
        "estado_rol": "no evaluado",
        "agua": "no evaluado",
        "agua_ok": None,
        "luz": "no evaluado",
        "luz_ok": None,
        "fecha_publicacion": "2026-08-03 (fecha de reenvio)",
        "veredicto": "No cumple",
        "puntaje": 1,
        "justificacion_puntaje": (
            "Ensenada pertenece a la comuna de Puerto Varas, Region de Los Lagos: no es Isla "
            "de Chiloe ni cordillera de Nuble. El analisis se detiene ahi, como corresponde. "
            "Aunque estuviera en zona, 1.600 UF son del orden de $65 millones, cuatro a cinco "
            "veces el techo del proyecto."
        ),
        "riesgos": [
            "Zona de riesgo volcanico: Ensenada esta en el area de influencia del volcan "
            "Calbuco, que hizo erupcion en 2015 y afecto directamente ese sector.",
        ],
        "datos_faltantes": [],
        "comparacion_zona": "No aplica: fuera de las zonas objetivo.",
        "primera_vez": "2026-08-03T19:27:00",
        "visto_ultima_vez": "2026-08-03T19:27:00",
        "veces_visto": 1,
        "_error": None,
    },
    {
        "id": "wa-portalterreno-sjlc",
        "url": "https://www.instagram.com/p/DVOCIOQjBx5/",
        "fuente": "Instagram - PortalTerreno (reenviado por Marcelo)",
        "titulo": "Parcelas en San Juan de La Costa desde 5.000 m2",
        "ubicacion_comuna": "San Juan de La Costa, provincia de Osorno",
        "zona": "Fuera de zona",
        "superficie": "5.000 m2",
        "precio_clp": 11990000,
        "precio_texto": "$11.990.000",
        "forma_pago": "dato faltante",
        "cumple_contado": None,
        "estado_rol": "no evaluado",
        "agua": "no evaluado",
        "agua_ok": None,
        "luz": "no evaluado",
        "luz_ok": None,
        "fecha_publicacion": "2026-08-03 (fecha de reenvio)",
        "veredicto": "No cumple",
        "puntaje": 1,
        "justificacion_puntaje": (
            "San Juan de la Costa esta en la provincia de Osorno, en el continente. Es facil "
            "confundirla con Chiloe porque comparte paisaje costero y region, pero no es la "
            "isla. El precio es atractivo y la superficie correcta, pero la zona no califica y "
            "el criterio no admite excepciones geograficas."
        ),
        "riesgos": [
            "El aviso es de un portal agregador que pide 'cotizar' para entregar informacion: "
            "no publica ni comuna exacta, ni rol, ni factibilidades. Sin esos datos no se puede "
            "evaluar nada aunque la zona calificara.",
        ],
        "datos_faltantes": [],
        "comparacion_zona": "No aplica: fuera de las zonas objetivo.",
        "primera_vez": "2026-08-03T19:40:00",
        "visto_ultima_vez": "2026-08-03T19:40:00",
        "veces_visto": 1,
        "_error": None,
    },
]


if __name__ == "__main__":
    datos = almacen.cargar()
    nuevas = almacen.agregar(datos, FICHAS)
    almacen.registrar_corrida(datos, {
        "fecha": "2026-08-03T19:45:00",
        "revisados": 3,
        "nuevos": len(nuevas),
        "evaluados": 3,
        "fuentes": 1,
        "errores": [],
        "uf_valor": 40500,
        "uf_estimada": True,
        "duracion_s": 0,
        "nota": "Carga inicial: avisos enviados por Marcelo Quinones via WhatsApp.",
    })
    almacen.guardar(datos)
    print(f"Historico sembrado: {len(datos['avisos'])} avisos ({len(nuevas)} nuevos).")
