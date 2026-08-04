"""
Historico de avisos evaluados.

Es un JSON plano versionado en el repo: cada corrida lo actualiza y hace commit.
Asi el sistema recuerda que ya vio (no repite avisos) y puede comparar precios
por zona a lo largo del tiempo, que es lo que pide el criterio de puntaje.
"""

import json
import os
from datetime import datetime
from pathlib import Path

RUTA = Path(__file__).parent / "site" / "data.json"


def cargar() -> dict:
    if not RUTA.exists():
        return {"avisos": [], "corridas": [], "actualizado": None}
    try:
        with open(RUTA, encoding="utf-8") as f:
            d = json.load(f)
        d.setdefault("avisos", [])
        d.setdefault("corridas", [])
        return d
    except (json.JSONDecodeError, OSError):
        return {"avisos": [], "corridas": [], "actualizado": None}


def ids_conocidos(datos: dict) -> set[str]:
    return {a.get("id") for a in datos["avisos"] if a.get("id")}


def agregar(datos: dict, fichas: list[dict]) -> list[dict]:
    """
    Suma fichas nuevas. Devuelve solo las que efectivamente son nuevas
    (las que ya existian se actualizan pero no se reportan como novedad).
    """
    por_id = {a["id"]: a for a in datos["avisos"] if a.get("id")}
    ahora = datetime.now().isoformat(timespec="seconds")
    nuevas = []

    for f in fichas:
        fid = f.get("id")
        if not fid:
            continue
        if fid in por_id:
            previo = por_id[fid]
            f["primera_vez"] = previo.get("primera_vez", ahora)
            f["visto_ultima_vez"] = ahora
            f["veces_visto"] = previo.get("veces_visto", 1) + 1
            # Si el precio cambio, lo dejamos registrado: es una senal util
            if previo.get("precio_clp") and f.get("precio_clp") and \
               previo["precio_clp"] != f["precio_clp"]:
                f.setdefault("historial_precio", previo.get("historial_precio", []))
                f["historial_precio"].append(
                    {"fecha": ahora, "antes": previo["precio_clp"], "ahora": f["precio_clp"]}
                )
            por_id[fid] = f
        else:
            f["primera_vez"] = ahora
            f["visto_ultima_vez"] = ahora
            f["veces_visto"] = 1
            por_id[fid] = f
            nuevas.append(f)

    datos["avisos"] = sorted(
        por_id.values(), key=lambda a: a.get("primera_vez", ""), reverse=True
    )
    datos["actualizado"] = ahora
    return nuevas


def registrar_corrida(datos: dict, resumen: dict) -> None:
    datos["corridas"].insert(0, resumen)
    datos["corridas"] = datos["corridas"][:90]  # 90 dias de bitacora


def guardar(datos: dict) -> None:
    os.makedirs(RUTA.parent, exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)

    # Copia embebida como JS: permite abrir la web con doble clic desde el
    # escritorio (file://), donde el navegador bloquea fetch de data.json.
    with open(RUTA.parent / "data.js", "w", encoding="utf-8") as f:
        f.write("window.DATOS_EMBED=")
        json.dump(datos, f, ensure_ascii=False)
        f.write(";")


def estadisticas_zona(datos: dict, zona: str) -> dict | None:
    precios = [
        a["precio_clp"] for a in datos["avisos"]
        if a.get("zona") == zona and isinstance(a.get("precio_clp"), (int, float))
    ]
    if not precios:
        return None
    precios.sort()
    return {
        "n": len(precios),
        "min": precios[0],
        "mediana": precios[len(precios) // 2],
        "max": precios[-1],
    }
