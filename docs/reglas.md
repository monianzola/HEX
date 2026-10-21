# Reglas de Hex

Hex es un juego de tablero para **dos jugadores**, por turnos, de **información perfecta** (los dos ven todo el tablero) y **sin azar**. Lo inventaron Piet Hein (1942) y John Nash (1948) de forma independiente.

## El tablero

Un rombo de **N×N casillas hexagonales**. En hex-arena el tamaño es configurable: 11×11 por defecto y 7×7 en el torneo.

```
    a b c d e
 0  . . . . .
 1   . . . . .
 2    . . . . .
 3     . . . . .
 4      . . . . .
```

Cada fila está desplazada media casilla a la derecha respecto a la anterior.

## Los jugadores

| Jugador | Número | Objetivo | Empieza |
|---|---|---|---|
| 🔴 **Rojo** | `1` | Conectar el borde de **arriba** (fila 0) con el de **abajo** (fila N-1) | Sí |
| 🔵 **Azul** | `2` | Conectar el borde de la **izquierda** (columna 0) con el de la **derecha** (columna N-1) | No |

## Cómo se juega

1. Empieza el Rojo. Después los jugadores se alternan.
2. En su turno, cada jugador coloca **una ficha** de su color en **cualquier casilla vacía**.
3. Las fichas no se mueven ni se retiran nunca.
4. Gana quien forme primero una **cadena continua** de fichas propias que una sus dos bordes.

!!! note "Sin regla del pastel"
    En el Hex de competición existe la *regla del pastel*: el segundo jugador puede quedarse con la primera jugada del rival, para compensar la ventaja de empezar. hex-arena **no** la implementa, para mantener el juego simple.

## Vecinos de una casilla

Cada casilla interior tiene **6 vecinas**. Con coordenadas `(fila, columna)`, las vecinas de `(r, c)` son:

| Dirección | Casilla |
|---|---|
| arriba-izquierda, arriba-derecha | `(r-1, c)`, `(r-1, c+1)` |
| izquierda, derecha | `(r, c-1)`, `(r, c+1)` |
| abajo-izquierda, abajo-derecha | `(r+1, c-1)`, `(r+1, c)` |

!!! warning "Ojo con las diagonales"
    `(r-1, c-1)` y `(r+1, c+1)` **no** son vecinas: en un tablero hexagonal están a distancia 2.

En los bordes hay menos vecinas: 4 en un lado, 3 en las esquinas obtusas y 2 en las agudas, `(0, 0)` y `(N-1, N-1)`.

## En Hex nunca hay empate

Si el tablero se llena, **exactamente uno** de los dos jugadores habrá conectado sus bordes. Es un teorema clásico, equivalente al teorema del punto fijo de Brouwer. La idea intuitiva es que la única forma de impedir que el Rojo cruce de arriba abajo es construir una barrera azul de izquierda a derecha, y esa barrera es justo una victoria del Azul.

Además, se demuestra que **el primer jugador tiene una estrategia ganadora** (argumento del *robo de estrategia* de Nash), aunque no se conoce cuál es para tableros grandes.

## Movimientos en hex-arena

Un movimiento es una tupla `(fila, columna)` con índices desde 0. Son **ilegales**, y lanzan `IllegalMoveError`:

- jugar en una casilla ocupada;
- jugar fuera del tablero;
- jugar cuando la partida ya ha terminado;
- usar algo que no sea una tupla de dos enteros.
