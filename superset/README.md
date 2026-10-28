# Superset del Observatorio

El tablero público (dashboard 1, embebido en la landing) está definido como código. Git es la fuente de
verdad: no se edita a mano en la interfaz de Superset (los cambios manuales se pierden al reconstruir).

| Archivo | Qué hace |
|---|---|
| `vistas_observatorio.sql` | Vistas `obs_*` en Supabase: capa de datos compartida por Superset y la landing |
| `aplicar_vistas.py` | Recrea las vistas en una sola transacción (rol propietario, `.env` local) |
| `construir_tablero.py` | Datasets, gráficos (por clave estable), diseño, filtros, colores y permisos de lectura |
| `ejecutar_en_servidor.sh` | Ejecuta un script dentro del contenedor de Superset en Hetzner con las credenciales del servidor |
| `recortar_publico.py`, `verificar_acceso_publico.py` | Recorte del rol Public (26-oct-2026) y su verificación |

## Reconstruir

```bash
.venv/bin/python superset/aplicar_vistas.py                   # 1. vistas
superset/ejecutar_en_servidor.sh superset/construir_tablero.py # 2. tablero (idempotente)
```

## Reglas

- **Regla de oro:** ninguna cifra escrita a mano en textos ni plantillas; todo sale de las vistas, con su n
  en la tabla *Base de cálculo*.
- Conteos de **ofertas distintas**; salario ausente = NULL (nunca cero).
- Superset no permite subconsultas en el SQL de un gráfico: la lógica va en las vistas (p. ej. `es_ultimo_mes`).
- El usuario de la API (`claude_api`, rol Alpha) y el rol Public solo ven un tablero si pueden leer algún
  dataset de sus gráficos: `construir_tablero.py` concede esa lectura (Public: solo estos datasets).
- Colores: paleta categórica validada (skill dataviz) fijada por entidad en `label_colors`.
- En teléfonos Superset no reorganiza el diseño: la landing muestra un resumen y un enlace al tablero.
