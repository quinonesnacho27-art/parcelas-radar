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

## Instalación (una sola vez, ~20 minutos)

### 1. Subir el proyecto a GitHub

Crea un repositorio nuevo llamado `parcelas-radar` y sube esta carpeta completa.
Puede ser público o privado; si es privado, GitHub Pages requiere cuenta de pago, así que
para la web conviene público (no hay nada sensible: las claves van en Secrets, nunca en el código).

### 2. Conseguir la clave de la API de Claude

Entra a [console.anthropic.com](https://console.anthropic.com) → **API Keys** → crear una nueva.
Cárgale saldo. El consumo esperado es de unos pocos dólares al mes: el prefiltro descarta
la mayoría de los avisos antes de llamar al modelo, y hay un tope de 25 evaluaciones por corrida.

### 3. Crear la contraseña de aplicación de Gmail

GitHub necesita poder enviar el correo. Tu contraseña normal de Gmail no sirve para esto
y **nunca** debe ir en el código:

1. La cuenta de Gmail que enviará los correos necesita la verificación en dos pasos activada.
2. Anda a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Crea una contraseña de aplicación, nómbrala "Parcelas Radar".
4. Google te muestra 16 caracteres. Cópialos: solo se ven una vez.

Esa contraseña sirve únicamente para enviar correo por SMTP y la puedes revocar cuando
quieras desde la misma página.

### 4. Cargar los secretos en GitHub

En el repositorio: **Settings → Secrets and variables → Actions → New repository secret**.

| Nombre | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | la clave del paso 2 |
| `GMAIL_USER` | la dirección de Gmail que envía (ej. `quinonesnacho27@gmail.com`) |
| `GMAIL_APP_PASSWORD` | los 16 caracteres del paso 3 |

En la pestaña **Variables** de esa misma página, agrega:

| Nombre | Valor |
|---|---|
| `URL_WEB` | `https://TU-USUARIO.github.io/parcelas-radar/` |

### 5. Activar GitHub Pages

**Settings → Pages → Source: GitHub Actions.** Eso es todo; el workflow publica solo.

### 6. Probarlo

**Actions → Informe diario de parcelas → Run workflow.**

En dos o tres minutos debería llegar el correo. Si algo falla, el log del workflow dice
exactamente qué: no falla en silencio.

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
correo.py       Arma y envía el correo HTML.
main.py         Orquesta la corrida diaria.
semilla.py      Carga inicial: los avisos que mandó Marcelo por WhatsApp.
fixtures.py     Los mismos avisos, como datos de prueba.
site/index.html La web: filtros, comparación por zona y calculadora.
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
