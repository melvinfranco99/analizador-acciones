# Analizador de acciones — Top 10 (3 meses)

Descarga datos publicos de mercado (Yahoo Finance, via `yfinance`) para el
universo S&P 500 + Nasdaq 100, calcula un analisis tecnico y fundamental de
cada accion, y muestra las 10 mejores oportunidades del momento con un precio
objetivo a 3 meses y un stop loss.

**No es asesoramiento financiero.** Es una herramienta educativa que automatiza
un proceso de screening; los datos y calculos pueden contener errores o retrasos.
Verifica siempre en tu broker (por ejemplo Trade Republic) antes de operar.

El proyecto tiene **dos formas de uso**:

- **Local con Flask** (`app.py`): analisis en vivo bajo demanda, en tu maquina.
- **Web publica estatica** (`docs/`, pensada para GitHub Pages): un
  [GitHub Action](.github/workflows/update-data.yml) regenera `docs/data.json`
  cada 6 horas (o al lanzarlo a mano) y la pagina estatica simplemente lo lee.
  GitHub Pages no puede ejecutar Python, asi que en esta version los datos
  no son "en directo" sino la ultima instantanea generada por el Action.

## Instalacion

Requiere Python 3.10+. Se recomienda un entorno virtual para no tocar los
paquetes globales de tu sistema:

```bash
python -m venv venv
venv\Scripts\activate        # en PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```bash
python app.py
```

(si usaste el entorno virtual, actívalo primero: `venv\Scripts\activate`)

Se abrira automaticamente `http://127.0.0.1:5000` en tu navegador. Pulsa
**«Actualizar analisis»** para lanzar una ejecucion en vivo (tarda entre 1 y 2
minutos, ya que descarga precios y fundamentales de cientos de tickers).

### Version estatica (GitHub Pages)

Para regenerar manualmente el `docs/data.json` que usa la version publica:

```bash
python generate_data.py
```

En GitHub, el workflow `.github/workflows/update-data.yml` hace lo mismo
automaticamente cada 6 horas y hace commit del resultado. Tambien se puede
lanzar a mano desde la pestaña **Actions** del repositorio ("Run workflow").

## Como funciona

1. **Universo**: `engine/tickers.py` define ~550 tickers (S&P 500 + Nasdaq 100).
2. **Precios**: `engine/data.py` descarga 1 año de historico OHLCV para todo el
   universo en bloques, mas el S&P 500 (`^GSPC`) como referencia.
3. **Prefiltro tecnico**: `engine/technical.py` calcula SMA50/200, RSI14, MACD,
   ATR14 y fuerza relativa vs el indice; `engine/scoring.py` puntua cada accion
   y se preselecciona a los ~350 mejores candidatos tecnicos (evita pedir
   fundamentales de todo el universo, aunque en la practica cubre casi todos
   los tickers con datos validos).
4. **Fundamentales**: `engine/data.py` descarga en paralelo el PER, crecimiento
   de ingresos/beneficios, margenes, ROE y consenso de analistas de esos
   candidatos. `engine/fx.py` obtiene el tipo de cambio EUR/USD del momento.
5. **Score combinado**: 55% tecnico + 45% fundamental (el horizonte de 3 meses
   pesa mas el timing tecnico, sin ignorar la calidad del negocio).
6. **Precio objetivo (3 meses)**: toma la mejor de dos senales amortiguadas al
   50% — la mitad del retorno de los ultimos 3 meses (continuacion parcial del
   momentum), o la mitad del recorrido hasta el precio objetivo medio de
   analistas — en vez de promediarlas, ya que exigir que ambas sean extremas a
   la vez descartaba casi todas las oportunidades reales. Limitado a un rango
   de -15% / +35%.
7. **Filtro de rentabilidad minima**: solo se conservan las acciones cuyo
   potencial estimado a 3 meses supera un 5% mensual compuesto (~15.8% en 3
   meses). Pueden salir menos de 10 (o ninguna) si el mercado no ofrece mas
   oportunidades que cumplan el listón.
8. **Stop loss**: el mayor entre `precio - 2×ATR14` y el minimo de las ultimas
   20 sesiones, acotado a una perdida de entre el 4% y el 15%.
9. Las hasta 10 acciones con mayor score combinado que superan el umbral
   forman el panel principal ("Operaciones a considerar ahora").
10. **Cambios de opinion** (`engine/changes.py`): compara cada ejecucion con el
    estado guardado de la anterior para detectar entradas/salidas de la lista
    y revisiones de precio objetivo propias, y complementa con eventos reales
    de mercado (subidas/bajadas de analistas, sorpresas de resultados) de los
    ultimos 3 meses. Aparecen en el panel lateral como notificaciones — el
    panel principal siempre refleja el estado vigente.

## Limitaciones honestas

- Los datos vienen de Yahoo Finance via `yfinance`; puede haber retrasos,
  huecos o campos ausentes para algunos tickers (se descartan automaticamente).
- La lista de S&P 500 / Nasdaq 100 es una instantanea aproximada, no oficial.
- No se verifica automaticamente la disponibilidad de cada accion en Trade
  Republic (no existe una API publica para ello); la seleccion se centra en
  grandes cotizadas de EE. UU., que en su gran mayoria si estan disponibles.
- El precio objetivo y el stop loss son estimaciones estadisticas basadas en
  reglas explicitas, no predicciones garantizadas.
