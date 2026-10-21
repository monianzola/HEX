# Torneo y clasificación

hex-arena enfrenta automáticamente a **todos los bots del repositorio** y publica una clasificación.

!!! info "En desarrollo"
    El módulo de torneo (`hexarena.tournament`) y la publicación automática de la clasificación se están implementando. Esta página describe su funcionamiento previsto.

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

## Ejecutarlo en local

```bash
python -m hexarena.tournament
```

Genera los resultados en JSON y una página HTML con la tabla de clasificación.

## Publicación automática

Un workflow de GitHub Actions ejecuta el torneo en cada *push* a `main`, cada lunes y cuando se lanza a mano, y publica la clasificación en **GitHub Pages**. Así, al fusionar el PR de un bot nuevo, la clasificación se actualiza sola.
