"""
Carga completa del WhatsApp de Marcelo Quinones (viernes 31/07 a lunes 03/08 de 2026).

Todos los avisos que mando por la conversacion, evaluados uno por uno con los
criterios del proyecto. Los de zona valida llevan ficha completa; los de fuera de
zona se registran con el motivo del descarte para no volver a analizarlos.

Correr una vez:  python semilla_whatsapp.py
"""

import almacen

IG = "https://www.instagram.com/p/"


def ficha(**kw):
    """Valores por defecto para no repetir campos en cada aviso."""
    base = {
        "superficie": "dato faltante",
        "precio_clp": None,
        "precio_texto": "no publica precio",
        "forma_pago": "dato faltante - pedir al vendedor",
        "cumple_contado": None,
        "estado_rol": "dato faltante - pedir al vendedor",
        "agua": "dato faltante - pedir al vendedor",
        "agua_ok": None,
        "luz": "dato faltante - pedir al vendedor",
        "luz_ok": None,
        "fecha_publicacion": "reenviado por WhatsApp",
        "riesgos": [],
        "datos_faltantes": [],
        "comparacion_zona": "",
        "primera_vez": "2026-08-03T22:00:00",
        "visto_ultima_vez": "2026-08-03T22:00:00",
        "veces_visto": 1,
        "_error": None,
    }
    base.update(kw)
    return base


# Preguntas que hay que hacer siempre que el aviso no las responda
FALTA_TODO = [
    "Precio al contado y descuento respecto del credito directo",
    "Numero de rol de una parcela concreta para verificarlo en el SII",
    "Factibilidad de agua: pozo, vertiente o derecho constituido en la DGA",
    "Factibilidad electrica: hay poste en el deslinde o hay que costear la extension",
    "Copia del plano de subdivision aprobado y certificado del SAG",
]

FICHAS = [

    # ======================================================================
    # ISLA DE CHILOE - los que valen la pena mirar
    # ======================================================================
    ficha(
        id="ig-sur-nativo-ancud-9900",
        url=IG + "DbjIpwfMopU/",
        fuente="Instagram - Inmobiliario Sur Nativo",
        titulo="Solo quedan 6 parcelas a $9.900.000 en Ancud",
        ubicacion_comuna="Ancud",
        zona="Isla de Chiloe",
        superficie="dato faltante (el proyecto hermano publica 5.000 m2)",
        precio_clp=9900000,
        precio_texto="$9.900.000",
        forma_pago="Al contado, con beneficios adicionales por pagar al contado",
        cumple_contado=True,
        estado_rol="dato faltante en este aviso; el aviso hermano del mismo proyecto declara rol propio y aprobacion SAG",
        agua="dato faltante en este aviso; el aviso hermano declara agua de pozo",
        luz="dato faltante - pedir al vendedor",
        veredicto="Cumple con reservas",
        puntaje=4,
        justificacion_puntaje=(
            "Es el mejor aviso de todo el lote. Esta bajo el objetivo de $10 millones, "
            "es explicitamente al contado —que es justo lo que pide el criterio— y esta en "
            "Ancud, la comuna con mejor conectividad de Chiloe. Ademas el mismo vendedor "
            "publica otro aviso del proyecto de Ancud declarando agua de pozo, rol propio y "
            "aprobacion SAG, que es exactamente lo que falta confirmar aqui. Si al llamar "
            "resulta ser el mismo loteo, sube a 5."
        ),
        riesgos=[
            "La urgencia ('solo quedan 6', 'promocion hasta agotar stock') es tecnica de venta "
            "estandar en este rubro. No apures la decision por eso.",
            "Los beneficios por pagar al contado (kit camping, gift card de $500.000) valen "
            "bastante menos que un descuento equivalente en el precio. Pide el descuento en plata.",
        ],
        datos_faltantes=[
            "Es el mismo proyecto que el aviso de 'agua de pozo, rol propio y SAG' a minutos de Ancud",
            "Superficie exacta de las 6 parcelas que quedan",
            "Numero de rol de una de ellas para verificarlo en el SII",
            "Factibilidad electrica: hay poste en el deslinde",
            "Distancia real a Ancud en kilometros, no en minutos",
        ],
        comparacion_zona="El mas barato de Chiloe con precio confirmado y venta al contado. 24% mas barato que Coquiao ($13M).",
    ),

    ficha(
        id="ig-sur-nativo-ancud-pozo",
        url=IG + "DUjcH6mDBv2/",
        fuente="Instagram - Inmobiliario Sur Nativo",
        titulo="Parcelas a minutos de Ancud con agua de pozo y rol propio",
        ubicacion_comuna="A minutos de Ancud",
        zona="Isla de Chiloe",
        estado_rol="Rol propio y aprobacion SAG declarados en el aviso",
        agua="Agua de pozo declarada",
        agua_ok=True,
        forma_pago="Ofrece credito hipotecario; no publica precio de contado",
        veredicto="Cumple con reservas",
        puntaje=4,
        justificacion_puntaje=(
            "Es el unico aviso del lote que declara de entrada las tres cosas que mas cuesta "
            "conseguir: agua de pozo, rol propio y aprobacion SAG. Eso lo pone por delante de "
            "casi todo lo demas. El problema es que no publica precio, y sin precio no hay "
            "evaluacion posible. Es la primera llamada que hay que hacer."
        ),
        riesgos=[
            "Que el aviso ofrezca 'gestionar la compra con credito hipotecario' sugiere que el "
            "precio no es bajo. Los proyectos realmente baratos se venden al contado.",
        ],
        datos_faltantes=[
            "PRECIO - es el unico dato que falta y es el que decide todo",
            "Superficie de las parcelas",
            "Numero de rol para verificar en el SII",
            "El pozo esta construido y con prueba de caudal, o es solo factibilidad",
            "Factibilidad electrica",
        ],
        comparacion_zona="Sin precio no se puede comparar. Probablemente sea el mismo proyecto que el de $9.900.000.",
    ),

    ficha(
        id="ig-raiz-de-ulmo-dalcahue",
        url=IG + "DavSCz4scx4/",
        fuente="Instagram - Raiz de Ulmo",
        titulo="Tierra propia en Chiloe a 20 min de Dalcahue",
        ubicacion_comuna="A 20 minutos de Dalcahue",
        zona="Isla de Chiloe",
        estado_rol="Rol individual declarado",
        agua="Factibilidad hidrica declarada (no especifica si es pozo, vertiente o derecho constituido)",
        luz="Factibilidad electrica declarada",
        luz_ok=True,
        veredicto="Cumple con reservas",
        puntaje=4,
        justificacion_puntaje=(
            "Declara acceso, rol individual y factibilidad electrica e hidrica: en el papel es "
            "de los mas completos del lote. Dalcahue esta en la lista de comunas objetivo y a "
            "20 minutos sigue siendo razonable. Le falta lo mismo que a varios: precio. "
            "'Factibilidad hidrica' es ademas una formula vaga que hay que aterrizar."
        ),
        riesgos=[
            "'Factibilidad hidrica' no es lo mismo que un derecho de aprovechamiento de aguas "
            "constituido en la DGA. Hay que preguntar exactamente cual de los dos es.",
        ],
        datos_faltantes=[
            "PRECIO y superficie",
            "Que significa 'factibilidad hidrica': pozo construido, vertiente, o derecho DGA inscrito",
            "Numero de rol para verificar en el SII",
            "Estado del camino de acceso en invierno",
        ],
        comparacion_zona="Sin precio. Perfil tecnico comparable al mejor de Ancud.",
    ),

    ficha(
        id="ig-remate-molulco-castro",
        url=IG + "DbhA91CAZqK/",
        fuente="Instagram - Remate de Terrenos",
        titulo="Terrenos en Molulco desde $10.900.000, a 25 min de Castro",
        ubicacion_comuna="Molulco, comuna de Chonchi (a 25 min de Castro)",
        zona="Isla de Chiloe",
        precio_clp=10900000,
        precio_texto="Desde $10.900.000",
        forma_pago="Financiamiento directo; al contado regalan los gastos operacionales",
        cumple_contado=True,
        estado_rol="Rol propio listo para escriturar, segun el aviso",
        luz="Factibilidad electrica declarada",
        luz_ok=True,
        veredicto="Cumple con reservas",
        puntaje=3,
        justificacion_puntaje=(
            "Molulco pertenece a la comuna de Chonchi, zona valida, y estar a 25 minutos de "
            "Castro es buena ubicacion. Declara rol propio listo para escriturar y factibilidad "
            "electrica, y premia el pago al contado. Lo que lo frena en 3 es que el precio parte "
            "sobre el objetivo de $10 millones y que el aviso no dice una sola palabra sobre el "
            "agua, que es el criterio excluyente."
        ),
        riesgos=[
            "El aviso no menciona el agua. Es el unico criterio excluyente del proyecto: sin "
            "respuesta clara sobre esto, no avanza.",
            "'Remate' en el nombre de la cuenta es marketing, no un remate judicial. No supongas "
            "que hay urgencia real ni precio de liquidacion.",
        ],
        datos_faltantes=[
            "FACTIBILIDAD DE AGUA - es lo que decide si sigue en carrera",
            "Superficie de los terrenos",
            "Cuanto son los 'gastos operacionales' que regalan al contado",
            "Numero de rol para verificar en el SII",
        ],
        comparacion_zona="12% mas caro que el de Ancud ($9,9M) y 16% mas barato que Coquiao ($13M).",
    ),

    ficha(
        id="ig-global-terrenos-quemchi",
        url=IG + "DaVuNTOAOio/",
        fuente="Instagram - GLOBAL TERRENOS CHILE",
        titulo="Liquidacion: terrenos en Quemchi desde $6.900.000 al contado",
        ubicacion_comuna="Quemchi",
        zona="Isla de Chiloe",
        superficie="5.000 m2",
        precio_clp=6900000,
        precio_texto="Desde $6.900.000 pagando al contado",
        forma_pago="Al contado",
        cumple_contado=True,
        veredicto="Cumple con reservas",
        puntaje=3,
        justificacion_puntaje=(
            "Es el precio mas bajo de todo el lote en zona valida: $1.380 por m2, casi la mitad "
            "de la mediana de Chiloe. Quemchi esta en la lista de comunas y la superficie es la "
            "correcta. Pero ese mismo precio es el problema: cuando un terreno esta muy por "
            "debajo del resto de su zona y el aviso no explica por que, la explicacion suele "
            "estar en algo que no se publica. No declara rol, ni agua, ni luz."
        ),
        riesgos=[
            "PRECIO ANOMALO: a $1.380/m2 esta un 47% bajo la mediana de Chiloe sin que el aviso "
            "de ninguna razon. Las causas habituales son terreno sin acceso vehicular, sin "
            "factibilidad de agua, anegadizo, o subdivision no regularizada. Averigua cual es "
            "antes de entusiasmarte con el precio.",
            "'Liquidacion' y 'ultimos lotes disponibles' sin fecha de termino ni cantidad: es "
            "presion de venta, no informacion.",
            "No declara rol propio, que en Chiloe es el dato que mas se omite cuando no existe.",
        ],
        datos_faltantes=FALTA_TODO + [
            "POR QUE esta tan barato comparado con el resto de Chiloe",
            "Tiene acceso vehicular por camino publico o por servidumbre",
            "El terreno es plano y drenado, o tiene sectores anegadizos",
        ],
        comparacion_zona="El mas barato de la zona: 30% bajo Ancud ($9,9M) y 47% bajo Coquiao ($13M). Esa distancia hay que explicarla.",
    ),

    ficha(
        id="ig-parcelas-chiloe-6900",
        url=IG + "DZnmLNRgAz0/",
        fuente="Instagram - Parcelas en Chiloe",
        titulo="Parcelas en Chiloe desde $6.900.000, precio contado",
        ubicacion_comuna="Chiloe (no especifica comuna)",
        zona="Isla de Chiloe",
        precio_clp=6900000,
        precio_texto="Desde $6.900.000 precio contado, o 36 cuotas de $229.000",
        forma_pago="Precio contado disponible",
        cumple_contado=True,
        veredicto="Cumple con reservas",
        puntaje=2,
        justificacion_puntaje=(
            "El precio de contado esta bien y la modalidad es la correcta, pero el aviso no dice "
            "en que comuna de Chiloe esta, ni la superficie, ni el rol, ni el agua. Sin comuna no "
            "se puede ni siquiera confirmar que caiga dentro de las ocho comunas objetivo. Es un "
            "aviso para llamar, no para evaluar."
        ),
        riesgos=[
            "36 cuotas de $229.000 suman $8.244.000 frente a $6.900.000 al contado: un 19,5% mas "
            "caro. Es una tasa alta disfrazada de facilidad de pago.",
            "No indica comuna. Chiloe tiene comunas que no estan en la lista objetivo.",
        ],
        datos_faltantes=["COMUNA exacta"] + FALTA_TODO,
        comparacion_zona="Mismo precio que Quemchi ($6,9M), el piso de la zona.",
    ),

    ficha(
        id="ig-portalterreno-ancud-8690",
        url=IG + "DTOfdHZjLuK/",
        fuente="Instagram - PortalTerreno Chile",
        titulo="Parcelas en Ancud desde 5.000 m2 a $8.690.000",
        ubicacion_comuna="Ancud",
        zona="Isla de Chiloe",
        superficie="5.000 m2",
        precio_clp=8690000,
        precio_texto="$8.690.000",
        veredicto="Cumple con reservas",
        puntaje=2,
        justificacion_puntaje=(
            "Precio y superficie correctos, comuna valida. El problema es la fuente: "
            "PortalTerreno es un agregador que publica el precio como anzuelo y obliga a "
            "'cotizar' para entregar cualquier otro dato. No hay rol, ni agua, ni luz, ni "
            "vendedor identificable. Sirve como referencia de precio de mercado en Ancud, no "
            "como oportunidad evaluable."
        ),
        riesgos=[
            "Vendedor no identificable: el aviso es de un portal, no del dueno del loteo. No se "
            "puede hacer estudio de titulos sobre un anuncio.",
            "Al dejar los datos en 'cotizar' entras a una base de datos comercial. Espera "
            "llamados de varios proyectos, no solo de este.",
        ],
        datos_faltantes=["Quien es el vendedor real del loteo"] + FALTA_TODO,
        comparacion_zona="$1.738/m2 en Ancud. Util como referencia: confirma que hay oferta en Ancud bajo $10M.",
    ),

    ficha(
        id="ig-tarahuin-chonchi",
        url=IG + "DaEL1mOsjHk/",
        fuente="Instagram - Inmobiliario Sur Nativo",
        titulo="Aires de Tarahuin, Chonchi - promocion aniversario",
        ubicacion_comuna="Aires de Tarahuin, Chonchi (a minutos del Lago Tarahuin, Chonchi y Castro)",
        zona="Isla de Chiloe",
        forma_pago="Ofrece gastos operacionales gratis y $500.000 de descuento en las primeras 10 unidades",
        veredicto="Cumple con reservas",
        puntaje=2,
        justificacion_puntaje=(
            "Chonchi es zona valida y el proyecto llega con el terreno adelantado —frente "
            "cercado, porton de acceso, terrenos planos y limpios— lo que en la practica "
            "descuenta uno o dos millones de habilitacion. Pero no publica precio, ni "
            "superficie, ni rol, ni agua. Con lo que hay, no se puede evaluar mas."
        ),
        riesgos=[
            "El mismo vendedor publica dos avisos casi identicos de este proyecto con beneficios "
            "distintos. Confirma cual promocion esta vigente antes de decidir.",
        ],
        datos_faltantes=["PRECIO y superficie"] + FALTA_TODO,
        comparacion_zona="Sin precio publicado.",
    ),

    ficha(
        id="ig-inversiones-sur-quemchi-remate",
        url=IG + "DaksW7ws4HE/",
        fuente="Instagram - Inversiones en el sur",
        titulo="Remates de parcelas en Quemchi, Isla de Chiloe",
        ubicacion_comuna="Quemchi",
        zona="Isla de Chiloe",
        veredicto="Cumple con reservas",
        puntaje=2,
        justificacion_puntaje=(
            "Quemchi es zona valida, pero el aviso es una sola linea: ni precio, ni superficie, "
            "ni rol, ni agua. No hay nada que evaluar todavia. Queda registrado para preguntar."
        ),
        riesgos=[
            "La palabra 'remate' usada como gancho comercial, sin tribunal ni martillero "
            "identificado, no significa nada legalmente.",
        ],
        datos_faltantes=FALTA_TODO,
        comparacion_zona="Sin datos.",
    ),

    ficha(
        id="ig-inversiones-sur-quemchi-3ha",
        url=IG + "Dayan72st2O/",
        fuente="Instagram - Inversiones en el sur",
        titulo="Parcelas desde 3 hectareas en Quemchi, Chiloe",
        ubicacion_comuna="Quemchi",
        zona="Isla de Chiloe",
        superficie="Desde 3 hectareas (30.000 m2)",
        veredicto="Cumple con reservas",
        puntaje=2,
        justificacion_puntaje=(
            "Zona valida y superficie muy superior a la parcela tipica de 5.000 m2, lo que en "
            "principio es bueno. Pero sin precio no hay forma de saber si 3 hectareas caben en "
            "el presupuesto: a los precios por m2 de la zona, 30.000 m2 se irian bastante sobre "
            "los $14 millones."
        ),
        riesgos=[
            "Sobre 5.000 m2 la subdivision rural cambia de regimen. Verifica que este acogida a "
            "la normativa correcta y con SAG al dia.",
        ],
        datos_faltantes=["PRECIO - critico dado el tamano"] + FALTA_TODO,
        comparacion_zona="Sin precio.",
    ),

    # ======================================================================
    # CORDILLERA DE NUBLE
    # ======================================================================
    ficha(
        id="ig-tierra-magna-danicalqui",
        url=IG + "DaW15w8Ao2f/",
        fuente="Instagram - Tierra Magna Chile",
        titulo="Cumbres de Danicalqui, Region de Nuble, desde $12.990.000",
        ubicacion_comuna="Danicalqui, comuna de Pemuco, Region de Nuble",
        zona="Cordillera de Nuble",
        superficie="De 2 a 4,1 hectareas",
        precio_clp=12990000,
        precio_texto="Desde $12.990.000",
        forma_pago="Financiamiento directo, escritura inmediata. No publica precio de contado",
        cumple_contado=None,
        estado_rol="Rol propio declarado en el aviso",
        veredicto="Cumple con reservas",
        puntaje=3,
        justificacion_puntaje=(
            "Es el unico aviso de todo el lote en la Region de Nuble, y por eso vale la pena "
            "mirarlo aunque tenga peros. Ofrece 2 a 4,1 hectareas con rol propio por $12,99 "
            "millones, es decir entre $317 y $650 por m2: muy por debajo de cualquier precio "
            "por m2 de Chiloe. Los dos reparos son la comuna y el agua."
        ),
        riesgos=[
            "OJO CON LA COMUNA: Danicalqui esta en Pemuco, que no aparece en la lista del "
            "proyecto (San Fabian, Coihueco, Pinto, Las Trancas, Recinto). El sector cordillerano "
            "de Pemuco si esta dentro de la Reserva de la Biosfera Nevados de Chillan-Laguna del "
            "Laja, asi que podria calzar como 'sector cordillerano aledano de Nuble', pero esa "
            "es una decision que tienes que tomar tu, no yo.",
            "No dice nada sobre el agua, que es el criterio excluyente.",
            "'Financiamiento directo' y 'escritura inmediata' en el mismo aviso es una "
            "combinacion que conviene aclarar: escriturar antes de terminar de pagar es poco "
            "habitual y cambia bastante el riesgo de la operacion.",
            "Zona cordillerana de Nuble: pregunta por riesgo de incendio forestal y por el estado "
            "del camino en invierno.",
        ],
        datos_faltantes=[
            "Confirmar si Pemuco entra o no en el criterio de zona (decision de Nacho)",
            "FACTIBILIDAD DE AGUA",
            "Precio al contado",
            "Como funciona la 'escritura inmediata' con financiamiento directo: hay hipoteca a favor del vendedor",
            "Distancia real y estado del camino desde Chillan",
            "Factibilidad electrica",
        ],
        comparacion_zona="Primer aviso registrado en la Region de Nuble. Entre $317 y $650/m2, muy por debajo de los $1.380-$2.600/m2 de Chiloe.",
    ),

    # ======================================================================
    # SIN DATOS SUFICIENTES PARA UBICAR
    # ======================================================================
    ficha(
        id="ig-austral-choroihue",
        url=IG + "DbGQy9VsHxD/",
        fuente="Instagram - Desarrollo Inm. Austral",
        titulo="Proyecto Choroihue - inversion con plusvalia",
        ubicacion_comuna="Choroihue - no se pudo verificar la comuna desde el aviso",
        zona="Fuera de zona",
        veredicto="No cumple",
        puntaje=1,
        justificacion_puntaje=(
            "El aviso es puro discurso de inversion —'plusvalia que crece', 'tu patrimonio vale "
            "mas'— y no entrega un solo dato verificable: ni comuna, ni region, ni precio, ni "
            "superficie. No pude confirmar donde queda Choroihue con la informacion del aviso, "
            "asi que no puedo afirmar que este en zona valida. Si tu papa tiene el contacto, "
            "preguntar la comuna toma un minuto y lo reevaluo."
        ),
        riesgos=[
            "Un aviso que habla solo de plusvalia y no dice donde queda el terreno es, por si "
            "mismo, una senal para tomar con calma.",
        ],
        datos_faltantes=["Comuna y region exactas", "Precio", "Superficie"],
        comparacion_zona="No evaluable.",
    ),

    ficha(
        id="ig-austral-refugio",
        url=IG + "DYVZvCyDD4L/",
        fuente="Instagram - Desarrollo Inm. Austral",
        titulo="Tu Refugio a Precio Irrepetible",
        ubicacion_comuna="no indicada en el aviso",
        zona="Fuera de zona",
        veredicto="No cumple",
        puntaje=1,
        justificacion_puntaje=(
            "El aviso solo dice 'Tu Refugio a Precio Irrepetible'. No hay ubicacion, ni precio, "
            "ni superficie, ni nada. Es el ultimo que mando tu papa, a las 8:52 de la noche. "
            "Sin datos no hay evaluacion posible."
        ),
        datos_faltantes=["Todo: comuna, precio, superficie, rol, agua, luz"],
        comparacion_zona="No evaluable.",
    ),

    # ======================================================================
    # FUERA DE ZONA - registrados para no volver a analizarlos
    # ======================================================================
    *[
        ficha(
            id=f"ig-fz-{i}",
            url=IG + slug + "/",
            fuente=f"Instagram - {cuenta}",
            titulo=titulo,
            ubicacion_comuna=lugar,
            zona="Fuera de zona",
            precio_clp=precio,
            precio_texto=f"${precio:,.0f}".replace(",", ".") if precio else "no publica precio",
            veredicto="No cumple",
            puntaje=1,
            justificacion_puntaje=motivo,
            datos_faltantes=[],
            comparacion_zona="No aplica: fuera de las zonas objetivo.",
        )
        for i, (slug, cuenta, titulo, lugar, precio, motivo) in enumerate([
            ("DaoQV5ygMNe", "Corredora de propiedades",
             "Valle Lagunas, Aysen, desde $3.990.000",
             "Valle Lagunas, Region de Aysen", 3990000,
             "Aysen no es zona objetivo. El precio llama la atencion, pero $3,99 millones por una "
             "parcela en la Patagonia normalmente significa acceso solo en verano, sin luz y sin "
             "agua: el costo de habilitarla supera con creces el ahorro."),
            ("DZbYVePDG-h", "Experto en inversion inmobiliaria",
             "Terreno en la Patagonia desde $5.990.000",
             "Patagonia (no especifica comuna)", 5990000,
             "Patagonia no es zona objetivo. Ademas el aviso no dice en que comuna esta."),
            ("DY7wVsogL4z", "Inmobiliaria FL",
             "Parcela de 5.000 m2 en la Patagonia desde $6.990.000",
             "Patagonia (no especifica comuna)", 6990000,
             "Patagonia no es zona objetivo, aunque declare rol propio y aprobacion SAG."),
            ("DbJQH1wgkSO", "Surcapital Propiedades",
             "Parcela con acceso al lago desde $12 millones en la Patagonia",
             "Patagonia chilena", 12000000,
             "Patagonia no es zona objetivo."),
            ("DbfOep1AiCY", "Patagonia Broker",
             "Mirador Lago Pollux, a 42 km de Coyhaique",
             "Coyhaique, Region de Aysen", None,
             "Aysen no es zona objetivo. El pie de 10% con cuotas de $334.000 tampoco calza con el "
             "criterio de pago al contado."),
            ("DV_COJFAGpm", "Altaro consultorias",
             "Parcelas de 5.000 m2 con vista al Lago General Carrera",
             "Puerto Ibanez, Region de Aysen", 8000000,
             "Aysen no es zona objetivo."),
            ("DZsT0gkDC0k", "Venta de Parcelas",
             "Isla Huemules, 2,5 hectareas con acceso al mar",
             "Isla Huemules, Patagonia", 13491000,
             "Patagonia no es zona objetivo. Una isla privada agrega ademas un problema de acceso "
             "que no tiene solucion barata."),
            ("DbWESfSsHjY", "Venta de parcelas",
             "Parcelas de 5.000 m2 a 15 minutos de Lonquimay",
             "Lonquimay, Region de La Araucania", None,
             "La Araucania no es zona objetivo."),
            ("DaWEJxKMGGE", "Maihue Eco Proyectos",
             "Parcelas en la Araucania",
             "Region de La Araucania", None,
             "La Araucania no es zona objetivo."),
            ("DbGPtPYMJg9", "Pewmayen",
             "Pewmayen, junto al rio Liucura",
             "Rio Liucura, comuna de Pucon, Region de La Araucania", None,
             "El rio Liucura esta en Pucon, La Araucania: no es zona objetivo."),
            ("DaWlmw-AnFS", "Reserva Porma",
             "Terrenos desde 5.000 m2 junto al mar en Teodoro Schmidt",
             "Teodoro Schmidt, Region de La Araucania", 11990000,
             "La Araucania no es zona objetivo, pese a declarar rol propio y financiamiento directo."),
            ("Da09uzYgPyd", "El Avellano",
             "Terrenos con rol propio y aprobacion SAG",
             "Los Muermos, provincia de Llanquihue, Region de Los Lagos", None,
             "Los Muermos esta en el continente, provincia de Llanquihue: no es Isla de Chiloe."),
            ("DbBehb5sRGA", "Tu Proyecto de Vida",
             "Parcelas a minutos de Frutillar con rol propio y SAG",
             "Frutillar, Region de Los Lagos", None,
             "Frutillar esta en el continente, no en Chiloe."),
            ("DZFaj9cgLAx", "Biosfera Austral",
             "Modelo de inversion y conservacion habitable",
             "no indicada en el aviso", None,
             "El aviso no dice donde queda ni cuanto cuesta. No hay nada que evaluar."),
            ("Da3op4YABnp", "Remate de Terrenos",
             "Kit de paneles solares gratis al comprar al contado",
             "no indicada en el aviso", None,
             "El aviso es solo la promocion; no indica ubicacion ni precio. La misma cuenta publica "
             "el proyecto de Molulco, que si esta evaluado."),
        ])
    ],
]


if __name__ == "__main__":
    datos = almacen.cargar()
    nuevas = almacen.agregar(datos, FICHAS)
    almacen.registrar_corrida(datos, {
        "fecha": "2026-08-03T22:00:00",
        "revisados": 38,
        "nuevos": len(nuevas),
        "evaluados": len(FICHAS),
        "fuentes": 1,
        "errores": [],
        "uf_valor": 40500,
        "uf_estimada": True,
        "duracion_s": 0,
        "nota": "Carga completa del WhatsApp de Marcelo Quinones (viernes 31/07 a lunes 03/08).",
    })
    almacen.guardar(datos)

    en_zona = [f for f in datos["avisos"] if f["zona"] != "Fuera de zona"]
    print(f"Historico: {len(datos['avisos'])} avisos ({len(nuevas)} nuevos en esta carga).")
    print(f"En zona valida: {len(en_zona)}")
    print()
    for f in sorted(en_zona, key=lambda x: (-x["puntaje"], x.get("precio_clp") or 9e9)):
        precio = f"${f['precio_clp']:,.0f}".replace(",", ".") if f.get("precio_clp") else "sin precio"
        print(f"  {f['puntaje']}/5  {precio:>14}  {f['ubicacion_comuna'][:45]}")
