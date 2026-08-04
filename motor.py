"""
Selector del motor de evaluacion.

Tres opciones, en orden de menos a mas dependencias:

  reglas     Por defecto. No usa API, no necesita clave, no cuesta nada y no
             tiene limite de uso. Lee los seis datos del aviso con reglas.

  gemini     Capa gratuita de Google AI Studio: 1.500 consultas al dia sin
             tarjeta de credito. Agrega redaccion mas natural en la
             justificacion. Ojo: Google advierte que los prompts de la capa
             gratuita pueden usarse para mejorar sus productos. Para avisos
             publicos de parcelas eso es de bajo riesgo, pero conviene saberlo.

  anthropic  API de pago de Claude. La mejor redaccion, unos pocos dolares al mes.

Se elige con la variable de entorno MOTOR, o en config.py.
Si el motor elegido falla —sin clave, sin cuota, sin red— cae automaticamente a
reglas y lo deja anotado en la ficha. La corrida diaria nunca se pierde por esto.
"""

import logging
import os

import evaluador_reglas

log = logging.getLogger("motor")

MOTOR = (os.environ.get("MOTOR") or "").strip().lower() or None


def _elegido() -> str:
    if MOTOR:
        return MOTOR
    try:
        from config import MOTOR_EVALUACION
        return (MOTOR_EVALUACION or "reglas").lower()
    except ImportError:
        return "reglas"


def evaluar(aviso: dict, historico=None, uf_valor=None) -> dict:
    m = _elegido()

    if m == "reglas":
        return evaluador_reglas.evaluar(aviso, historico, uf_valor)

    if m == "gemini":
        try:
            import evaluador_gemini
            ficha = evaluador_gemini.evaluar(aviso, historico, uf_valor)
            if not ficha.get("_error"):
                return ficha
            log.warning("Gemini fallo (%s); se usa el motor de reglas", ficha["_error"])
        except Exception as e:  # noqa: BLE001
            log.warning("Gemini no disponible (%s: %s); se usa el motor de reglas",
                        type(e).__name__, e)

    elif m == "anthropic":
        try:
            import evaluador
            ficha = evaluador.evaluar(aviso, historico, uf_valor)
            if not ficha.get("_error"):
                return ficha
            log.warning("Claude fallo (%s); se usa el motor de reglas", ficha["_error"])
        except Exception as e:  # noqa: BLE001
            log.warning("Claude no disponible (%s: %s); se usa el motor de reglas",
                        type(e).__name__, e)

    else:
        log.warning("Motor '%s' desconocido; se usa el motor de reglas", m)

    ficha = evaluador_reglas.evaluar(aviso, historico, uf_valor)
    ficha["_motor"] = "reglas (respaldo)"
    return ficha
