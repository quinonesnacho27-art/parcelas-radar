# Parcelas Radar

Sistema automático que revisa todos los días los avisos nuevos de parcelas en la
**cordillera de Ñuble** y la **Isla de Chiloé**, los evalúa contra los criterios de
inversión definidos, y manda un correo a `jmqs2007@gmail.com` con las fichas listas.

Además publica una página web con el historial completo, filtros y una calculadora de
costos vs. rentabilidad, que se abre igual desde el celular o el computador.

---

## Antes de empezar: qué hace y qué no hace

**Sí hace, solo y sin intervención:**

- Revisa Portalinmobiliario y Yapo todos los días a las 8 AM.
- Filtra por zona y precio *antes* de gastar dinero en la API (así el costo se mantiene bajo).
- Evalúa cada aviso con Claude usando exactamente los criterios del proyecto: uso de
  inversión, precio, pago al contado, rol propio del SII, agua obligatoria, luz deseable.
- Guarda el historial para poder comparar precios de la misma zona en el tiempo.
- Manda el correo y actualiza la web.

**No hace, y es importante que lo sepas:**

- **No lee Instagram ni Facebook Marketplace automáticamente.** Meta no tiene API pública
  de avisos y raspar sus páginas viola sus términos de servicio: en la práctica termina en
  cuentas bloqueadas y datos poco confiables, además del problema legal. No construí esa
  parte a propósito.
  La vía que sí funciona está resuelta abajo, en **[Avisos de Instagram y Facebook](#avisos-de-instagram-y-facebook)**:
  se reenvían por correo y entran al mismo pipeline, con la misma ficha y el mismo puntaje.
- **No verifica nada en el SII, el CBR ni la DGA.** Lee lo que dice el aviso. Si el aviso
  miente, el sistema repite la mentira — por eso cada ficha incluye una lista explícita de
  qué hay que preguntarle al vendedor.

---

## Estado actual

La web ya está publicada y funcionando:
**https://quinonesnacho27-art.github.io/parcelas-radar/**

Ya está hecho: el repositorio, el código, los dos workflows, GitHub Pages activado, la
variable `URL_WEB`, el secret `GMAIL_USER` y la carga inicial de 31 avisos evaluados.

**Falta solo un paso, y tiene que hacerlo Nacho** porque son credenciales: cargar dos
secrets. Sin ellos la web funciona igual, pero el correo diario no sale.

---

## El paso que falta (5 minutos)

### 1. Clave de la API de Claude

[console.anthropic.com](https://console.anthropic.com) → **API Keys** → crear una nueva y
cargarle saldo. El consumo esperado es de unos pocos dólares al mes: el prefiltro descarta
la mayoría de los avisos antes de llamar al modelo y hay un tope de 25 evaluaciones por corrida.

### 2. Contraseña de aplicación de Gmail

Tu contraseña normal de Gmail no sirve para esto y **nunca** debe ir en el código:

1. La cuenta necesita la verificación en dos pasos activada.
2. Anda a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Crea una contraseña de aplicación y nómbrala "Parcelas Radar".
4. Google te muestra 16 caracteres. Cópialos: solo se ven una vez.

Sirve únicamente para enviar correo por SMTP y la puedes revocar cuando quieras desde esa
misma página.

### 3. Cargar los dos secrets

En [Settings → Secrets and variables → Actions](https://github.com/quinonesnacho27-art/parcelas-radar/settings/secrets/actions)
→ **New repository secret**:

| Nombre | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | la clave del paso 1 |
| `GMAIL_APP_PASSWORD` | los 16 caracteres del paso 2 |

### 4. Probarlo

[Actions → Informe diario de parcelas → Run workflow](https://github.com/quinonesnacho27-art/parcelas-radar/actions/workflows/diario.yml).
En dos o tres minutos debería llegar el correo a jmqs2007@gmail.com. Si algo falla, el log
del workflow dice exactamente qué: no falla en silencio.

---

## Referencia: cómo se armó

Por si alguna vez hay que rehacerlo desde cero o moverlo a otra cuenta:

1. Repositorio público en GitHub (público porque GitHub Pages gratis lo requiere; no hay
   nada sensible adentro — las claves viven en Secrets, nunca en el código).
2. **Settings → Pages → Source: GitHub Actions.**
3. **Settings → Secrets and variables → Actions**, pestaña *Variables*: `URL_WEB` con la
   URL de la web. Pestaña *Secrets*: `GMAIL_USER`, `GMAIL_APP_PASSWORD` y `ANTHROPIC_API_KEY`.
4. Dos workflows separados a propósito: `publicar.yml` sube la web en cada push a `site/`,
   y `diario.yml` corre el informe a las 8 AM. Van separados para que la web siga
   disponible aunque la corrida diaria falle.
5. `python semilla_whatsapp.py` para cargar el historial inicial.

---

## Cómo se ordenan las parcelas

Lo que manda es **precio, rol y agua**. La localidad es el segundo criterio: desempata, no decide.

Los tres criterios duros suman 100 puntos:

| Criterio | Situación | Puntos |
|---|---|---|
| **Precio** (40) | Hasta $10.000.000 | 40 |
| | Entre $10 y $14 millones | 40 → 20 |
| | No publica precio | 4 |
| | Sobre $14.000.000 | 0 |
| **Rol** (30) | Verificado en el SII | 30 |
| | Rol propio declarado en el aviso | 22–24 |
| | Dato faltante | 3 |
| | Sin rol propio | 0 |
| **Agua** (30) | Derecho constituido en la DGA o red | 30 |
| | Pozo declarado | 26 |
| | Vertiente o "factibilidad hídrica" | 18 |
| | Dato faltante | 2 |
| | Sin factibilidad | 0 |

Un dato faltante suma casi cero, y es a propósito: un aviso con buen precio que no dice
nada del rol ni del agua no es mejor que uno con rol y agua resueltos.

El listado se agrupa por cuántos de los tres criterios responde el aviso —los tres, dos,
o menos— así se entiende el orden sin mirar el puntaje.

La localidad se ordena por conectividad y servicios, que es lo que sostiene la plusvalía:
Ancud, Castro, Las Trancas, Recinto y Pinto arriba; Dalcahue, Chonchi, Quellón, San Fabián
y Coihueco al medio; Quemchi, Curaco de Vélez y Puqueldón abajo. Es un juicio explícito y
editable en `prioridad.py → LOCALIDADES`, no un dato objetivo.

---

## Avisos de Instagram y Facebook

Esta es la parte que reemplaza al scraping imposible, y funciona bien porque el trabajo
humano se reduce a reenviar un mensaje.

**Configuración (una vez):** en Gmail, crea la etiqueta `ParcelasRadar`. Después crea un
filtro (**Configuración → Filtros → Crear un filtro**) que aplique esa etiqueta
automáticamente a los correos que lleguen desde tu papá, o que tengan cierta palabra en
el asunto — lo que te acomode más.

**Uso diario:** cuando tu papá vea una parcela en Instagram o Marketplace, toca *Compartir
→ Correo* y la manda. A la mañana siguiente aparece evaluada en el informe, junto a las
demás, con su puntaje y sus advertencias.

El sistema reconoce solo el link y lo clasifica como Instagram, Facebook Marketplace o
reenvío genérico, así que sabes de dónde salió cada ficha.

---

## Cómo usarlo día a día

**Tu papá** recibe el correo. Cada parcela viene como una tarjeta con veredicto
(*Cumple* / *Cumple con reservas* / *No cumple*), puntaje de 1 a 5, la ficha completa, las
advertencias en rojo y las preguntas concretas que hay que hacerle al vendedor. Abajo hay
un botón que lleva a la web.

**En la web** puede filtrar por zona, precio máximo, veredicto, o exigir que tenga rol
propio / agua confirmada / venta al contado. La pestaña *Precios por zona* muestra la
mediana de cada zona, que es la referencia para saber si un aviso está caro.

**La calculadora** es la parte que más cambia decisiones. Toma el precio del aviso y le
suma lo que realmente cuesta dejar la parcela usable: gastos de compraventa, pozo,
electrificación, cierre, mantención anual, comisión de corretaje e impuesto a la ganancia.

Un ejemplo con la parcela real de Coquiao, Ancud:

| | |
|---|---|
| Precio del aviso | $13.000.000 ($2.600/m²) |
| Inversión total real | **$22.940.000 ($4.588/m²)** |
| Valor de venta a 5 años, 8% anual | $31.296.688 |
| Ganancia neta | $6.850.644 |
| **Rentabilidad anualizada** | **5,4% anual** |

El aviso se ve como una parcela de $13 millones. Con la habilitación adentro, cuesta casi
$23 millones, y a un 8% de plusvalía anual rinde 5,4% — bastante menos de lo que sugiere
el titular. Ese es exactamente el número que la calculadora existe para mostrar.

---

## Ajustar los criterios

Todo lo editable vive en **`config.py`**, y nada más hay que tocar:

- `ZONAS` — comunas y palabras clave de cada zona.
- `ZONAS_TRAMPA` — lugares que suenan a la zona pero no califican (Ensenada, San Juan de
  la Costa, Pucón…). Cada uno lleva la explicación que aparece en la ficha.
- `PRECIO_IDEAL_MAX` / `PRECIO_TOLERABLE_MAX` — los $10 y $14 millones.
- `BUSQUEDAS` — las consultas que se corren en cada portal. Agregar una comuna es agregar
  una línea.
- `DESTINATARIOS` — a quién le llega el correo.
- `MAX_EVALUACIONES_POR_CORRIDA` — el tope de gasto de API por día.

Para cambiar la hora del envío, edita el `cron` en `.github/workflows/diario.yml`.
GitHub trabaja en UTC: `"0 12 * * *"` son las 8 AM en Chile en horario de invierno.

---

## Probarlo en tu computador

```bash
pip install -r requirements.txt

python main.py --demo --sin-api --dry-run   # sin red, sin API, sin correo
python main.py --dry-run                    # busca y evalúa de verdad, pero no envía
python main.py                              # corrida completa
```

`--dry-run` deja la vista previa del correo en `ultimo_informe.html`: ábrela con doble
clic para ver exactamente cómo va a llegar.

Para ver la web sin subir nada:

```bash
cd site && python -m http.server 8000    # luego abre http://localhost:8000
```

También funciona abriendo `site/index.html` directo con doble clic, porque el historial se
guarda además en `data.js` para ese caso.

---

## Estructura

```
config.py       Criterios, zonas, precios, búsquedas. Lo único que se edita seguido.
filtro.py       Prefiltro barato: detecta zona y precio sin gastar API.
fuentes.py      Portalinmobiliario, Yapo, valor de la UF, ingesta por correo (IMAP).
evaluador.py    Llama a Claude con los criterios y devuelve la ficha estructurada.
almacen.py      Historial en site/data.json (+ data.js). Detecta cambios de precio.
prioridad.py    Clasifica precio/rol/agua y calcula el índice de 0 a 100.
correo.py       Arma y envía el correo HTML.
main.py         Orquesta la corrida diaria.
semilla_whatsapp.py  Carga inicial: los 31 avisos que mandó Marcelo por WhatsApp, evaluados.
semilla.py           Los tres primeros avisos (subconjunto del anterior).
fixtures.py          Datos de prueba para correr sin red ni API.
migrar.py            Recalcula la prioridad de todo el historial si cambian los pesos.
site/index.html      La web: filtros, comparación por zona y calculadora.
.github/workflows/   diario.yml (informe 8 AM) y publicar.yml (web en cada push a site/).
```

---

## Si algo deja de funcionar

Los portales cambian su HTML cada cierto tiempo y un scraper se rompe. El sistema está
hecho para degradarse sin colapsar: si una fuente falla, las demás siguen, el correo llega
igual y el informe incluye un recuadro amarillo que dice qué fuente tuvo problemas. Cuando
veas ese recuadro varios días seguidos, hay que actualizar los selectores en `fuentes.py`.

---

## Advertencia

Este sistema lee avisos publicados y aplica criterios de filtro. No verifica títulos, no
confirma roles en el SII, no revisa derechos de agua en la DGA ni comprueba que una
subdivisión esté autorizada. La calculadora proyecta escenarios con supuestos que tú
ingresas: no es una predicción ni asesoría financiera o tributaria.

Antes de comprometer dinero: estudio de títulos con abogado, verificación del rol en el
SII, revisión del plano de subdivisión aprobado y visita presencial al terreno.
