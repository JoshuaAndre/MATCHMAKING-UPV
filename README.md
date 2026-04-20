# MATCHMAKING-UPV

Plataforma de matchmaking basada en MMR para videojuegos, desarrollada con microservicios, Docker y PostgreSQL.

## Servicios del proyecto

- player-service
- matchmaking-service
- rating-service
- match-service

## Tecnologías usadas

- Python
- FastAPI
- Docker Compose
- PostgreSQL
- SQLAlchemy

## Flujo del sistema

1. Se registran jugadores en `player-service`.
2. Los jugadores entran a la cola en `matchmaking-service`.
3. Cuando hay dos jugadores, `matchmaking-service` crea una partida en `match-service`.
4. Al finalizar una partida, `match-service` consulta `rating-service`.
5. `rating-service` calcula el nuevo MMR.
6. `match-service` actualiza el nuevo MMR en `player-service`.

## Persistencia

- `player-service` guarda jugadores en PostgreSQL.
- `match-service` guarda partidas en PostgreSQL.
- `matchmaking-service` mantiene la cola en memoria.
- `rating-service` calcula resultados sin persistencia.

## Cómo ejecutar el proyecto

```bash
docker compose up --build -d# MATCHMAKING-UPV

Plataforma de matchmaking basada en MMR para videojuegos, construida con microservicios.

## Servicios

- player-service
- matchmaking-service
- rating-service
- match-service

## Objetivo del MVP

- Registrar jugadores
- Gestionar colas de matchmaking
- Emparejar jugadores por MMR
- Registrar partidas
- Actualizar MMR al finalizar partidas

## Estado actual

- [x] Repositorio creado
- [x] Issues creados
- [x] player-service funcional
- [ ] matchmaking-service
- [ ] rating-service
- [ ] match-service
- [ ] Docker en todos los servicios
- [ ] Helm
- [ ] GitHub Actions
- [ ] DigitalOcean

## Flujo funcional validado

1. Se crean dos jugadores en player-service.
2. Ambos jugadores entran a la cola en matchmaking-service.
3. matchmaking-service crea automáticamente una partida en match-service.
4. La partida se finaliza en match-service.
5. match-service consulta rating-service para recalcular el MMR.
6. match-service actualiza el nuevo MMR en player-service.

### Resultado de prueba
- PlayerOne: 1200 -> 1215
- PlayerTwo: 1180 -> 1165
