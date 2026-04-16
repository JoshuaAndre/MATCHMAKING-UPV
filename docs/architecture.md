# Arquitectura inicial

## player-service
Gestiona el registro y consulta de jugadores.

## matchmaking-service
Recibe jugadores en cola y busca emparejamientos por rango de MMR.

## rating-service
Calcula el nuevo MMR de los jugadores al finalizar una partida.

## match-service
Registra partidas, estado y resultados.

## Flujo del MVP

1. Se registra un jugador.
2. El jugador entra a cola.
3. El matchmaking-service busca rival.
4. Se crea la partida.
5. rating-service recalcula el MMR.
6. match-service guarda el resultado.