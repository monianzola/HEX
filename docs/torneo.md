# Torneo y clasificación

hex-arena enfrenta automáticamente a **todos los bots del repositorio** y publica una clasificación.

!!! success "Clasificación actual"
    👉 **[monianzola.github.io/HEX](https://monianzola.github.io/HEX/)**: se regenera sola en cada cambio de `main` y cada lunes.

## Formato

| Parámetro | Valor |
|---|---|
| Sistema | **Round-robin**: cada bot juega contra todos los demás |
| Tablero | **7×7** (más rápido que 11×11 y suficiente para diferenciar bots) |
| Partidas por pareja | **20**: 10 con cada color, para compensar la ventaja de empezar |
| Tiempo | **1 segundo** por movimiento |
| Semilla | Fija, para que los resultados sean reproducibles |

## Clasificación

Para cada bot se calculan:

- **Victorias, derrotas** y **porcentaje de victorias**.
- **Elo**: todos empiezan con **1000** puntos. Tras cada partida, el ganador quita puntos al perdedor según la fórmula

    ```text
    esperado_A = 1 / (1 + 10 ** ((Elo_B - Elo_A) / 400))
    nuevo_Elo_A = Elo_A + K * (resultado_A - esperado_A)
    ```

    con **K = 32**, donde `resultado_A` vale 1 si A gana y 0 si pierde. Ganar a un rival con más Elo da más puntos que ganar a uno más débil.

## Robustez: un bot que falla no rompe el torneo

Cada movimiento se ejecuta con un límite de tiempo y aislado del resto. Un bot **pierde la partida**, se registra el motivo y el torneo continúa, si:

- lanza una excepción;
- tarda más del tiempo permitido o se queda colgado;
- devuelve un movimiento ilegal.

Cada bot vive en **su propio proceso** y recibe las peticiones por una tubería (`multiprocessing.Pipe`). El torneo espera cada respuesta como máximo `time_limit + 0,5 s`; si no llega, **mata el proceso** y lo vuelve a arrancar para la siguiente partida. Así, ni un bucle infinito ni un `os._exit()` pueden detener el torneo.

| Motivo registrado | Qué pasó |
|---|---|
| `connection` | Victoria normal: el ganador conectó sus bordes |
| `exception` | El bot lanzó una excepción (o no se pudo cargar/crear) |
| `timeout` | No respondió a tiempo |
| `illegal` | Devolvió una jugada ilegal o algo que no es una tupla `(fila, columna)` |
| `crash` | Su proceso murió |

## Ejecutarlo en local

```bash
python -m hexarena.tournament                      # configuración oficial
python -m hexarena.tournament --bots random shortest-path --size 5 --games 4 --time-limit 0.5
python -m hexarena.tournament --help               # todas las opciones
```

Genera `results/results.json` (resultados completos, partida a partida) y `results/index.html` (la página de clasificación). También se pueden incluir bots que no están registrados con su ruta de importación: `--bots random mi_paquete.mi_modulo:MiBot`.

## Referencia del API

::: hexarena.tournament.runner.run_tournament

::: hexarena.tournament.runner.TournamentConfig

::: hexarena.tournament.runner.GameRecord

::: hexarena.tournament.elo.update_elo

## Publicación automática

Un workflow de GitHub Actions ejecuta el torneo en cada *push* a `main`, cada lunes y cuando se lanza a mano, y publica la clasificación en **GitHub Pages**. Así, al fusionar el PR de un bot nuevo, la clasificación se actualiza sola.
