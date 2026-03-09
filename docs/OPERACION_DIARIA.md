# Operacion Diaria Mande24 Independent

## Objetivo
Guia rapida para validar operatividad de ERPMande24 y portales web en ambiente local.

## Pre-requisitos
- Docker Desktop activo.
- Puertos libres: `3000`, `8000`, `5432`, `6379`.
- Estar ubicado en la raiz del proyecto `mande24_independent`.

## Arranque Diario
```powershell
docker compose up -d
```

Verifica estado de servicios:
```powershell
docker compose ps
```

Resultado esperado: `api`, `web`, `postgres`, `redis` con estado `Up`.

## Validacion Rapida (Un Comando)
Ejecuta el smoke check completo:
```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/health-smoke.ps1
```

Resultado esperado al final:
- `=== RESULT: PASS ===`
- Reporte guardado en `scripts/reports/health-smoke-YYYYMMDD-HHMMSS.txt`.

Nota:
- Por defecto, el script limpia automaticamente los registros smoke (`customer_name = Smoke Script`) al finalizar.
- Si quieres conservar esos datos para inspeccion, usa `-SkipCleanupSmokeData`.

Ejemplo conservando datos smoke:
```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/health-smoke.ps1 -SkipCleanupSmokeData
```

## Validacion Manual de Portales
1. Auth: `http://localhost:3000/auth`
2. Cliente: `http://localhost:3000/client`
3. Rider: `http://localhost:3000/rider`
4. Estacion: `http://localhost:3000/station`
5. ERPMande24: `http://localhost:8000/ERPMande24`

Flujo recomendado:
1. Login en Auth.
2. Crear guia en Cliente.
3. Actualizar etapa en Rider con `delivery_id`.
4. Revisar comisiones en Estacion.
5. Confirmar registros en ERPMande24.

## Tarea de VS Code (Un Clic)
Ya existe la tarea:
- `Mande24: Health Smoke Check`

Como usarla:
1. `Ctrl+Shift+P`
2. Ejecutar `Tasks: Run Task`
3. Seleccionar `Mande24: Health Smoke Check`

## Diagnostico Basico
Ver logs API:
```powershell
docker compose logs -f api
```

Ver logs Web:
```powershell
docker compose logs -f web
```

Reiniciar stack:
```powershell
docker compose down
docker compose up -d --build
```

## Fallas Comunes
- `Connection refused` en `3000` o `8000`:
  - Verificar `docker compose ps` y puertos ocupados.
- `kind=error` en creacion de guia ERPMande24:
  - Ejecutar nuevamente `health-smoke.ps1` (activa servicio/estacion demo de forma automatica).
- Portal sin token:
  - Ir a `/auth` y autenticar para guardar `m24_token` en navegador.

## Cierre Diario
Opcional, para liberar recursos:
```powershell
docker compose down
```

## Smoke En Staging (CI)
Existe workflow:
- `.github/workflows/staging-smoke.yml`

Disparadores:
1. Manual (`workflow_dispatch`) con URLs personalizadas.
2. Automatico despues de `API Tests` o `Web Build` en rama `main` (si terminaron `success`).

Secrets recomendados en GitHub:
- `STAGING_API_BASE` (ejemplo: `https://api-staging.tudominio.com`)
- `STAGING_WEB_BASE` (ejemplo: `https://staging.tudominio.com`)

Proteccion recomendada del environment `staging`:
1. En GitHub, abrir `Settings > Environments`.
2. Crear environment `staging`.
3. Activar `Required reviewers` (al menos 1).
4. (Opcional) Activar `Wait timer` para ventana de validacion.

Nota:
- El workflow `staging-smoke.yml` ya apunta a `environment: staging`, por lo que respetara estas reglas automaticamente.

Notas:
- Por defecto en staging corre solo health de endpoints (`-SkipGuideFlow`) para no mutar datos.
- Si quieres flujo funcional de creacion de guia desde workflow manual, activa `run_guide_flow=true`.

## Renovar URLs Temporales (sin dominio)
Si usas `trycloudflare` (URLs temporales), ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/renew-staging-tunnels.ps1 -TriggerSmoke
```

Esto hace en automatico:
1. Abre tunel publico para API (puerto 8000).
2. Abre tunel publico para WEB (puerto 3000).
3. Actualiza secrets GitHub:
  - `STAGING_API_BASE`
  - `STAGING_WEB_BASE`
4. Dispara workflow `Staging Smoke`.
5. Cierra tuneles `cloudflared` previos que ya usaban esos puertos, para evitar procesos duplicados.

Opcional:
- Para ejecutar smoke con flujo de guia (mutacion), agrega `-RunGuideFlow`.
- Para NO cerrar tuneles previos automaticamente, agrega `-SkipStopExistingTunnels`.
