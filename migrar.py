"""Recalcula la prioridad de todo el historial con el criterio precio/rol/agua."""
import almacen, prioridad

datos = almacen.cargar()
for f in datos["avisos"]:
    prioridad.calcular(f)
datos["avisos"].sort(key=prioridad.clave_orden)
almacen.guardar(datos)

print(f"{len(datos['avisos'])} avisos recalculados\n")
print(f"{'IDX':>4} {'3/3':>4} {'LOC':>4} {'PRECIO':>13}  {'P':>2} {'R':>2} {'A':>2}  UBICACION")
print("-" * 88)
for f in datos["avisos"][:16]:
    p = f["prioridad"]
    precio = f"${f['precio_clp']:,.0f}".replace(",", ".") if f.get("precio_clp") else "sin precio"
    print(f"{p['indice']:>4} {'SI' if p['cumple_tres'] else '--':>4} {p['localidad']['nivel']:>4} "
          f"{precio:>13}  {p['precio']['puntos']:>2} {p['rol']['puntos']:>2} {p['agua']['puntos']:>2}  "
          f"{f['ubicacion_comuna'][:44]}")
