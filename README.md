# MATCHMAKING-UPV

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