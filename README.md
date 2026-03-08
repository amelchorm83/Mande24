# Mande24 Independent

Proyecto nuevo para correr Mande24 fuera de Odoo, con arquitectura lista para local -> staging -> produccion.

## Estructura

- `apps/api`: FastAPI
- `apps/web`: Next.js
- `docker-compose.yml`: stack local (api, web, postgres, redis)

## Arranque local

1. Copie variables:

```powershell
Copy-Item .env.example .env
```

2. Levante servicios:

```powershell
docker compose up --build
```

3. Pruebe endpoints:

- API health: `http://localhost:8000/api/v1/health`
- Web: `http://localhost:3000`

## Endpoints iniciales

- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/catalogs/services`
- `GET /api/v1/catalogs/services`
- `POST /api/v1/catalogs/zones`
- `GET /api/v1/catalogs/zones`
- `POST /api/v1/catalogs/stations`
- `GET /api/v1/catalogs/stations`
- `POST /api/v1/catalogs/riders`
- `GET /api/v1/catalogs/riders`
- `POST /api/v1/catalogs/pricing-rules`
- `GET /api/v1/catalogs/pricing-rules`
- `GET /api/v1/commissions/riders/weekly`
- `POST /api/v1/commissions/riders/weekly/close`
- `GET /api/v1/commissions/riders/weekly/history`
- `GET /api/v1/commissions/stations/weekly`
- `POST /api/v1/commissions/stations/weekly/close`
- `GET /api/v1/commissions/stations/weekly/history`
- `POST /api/v1/guides`
- `GET /api/v1/guides/{guide_code}`
- `GET /api/v1/guides/deliveries/{delivery_id}`
- `PATCH /api/v1/guides/deliveries/{delivery_id}/stage`

Regla aplicada: para marcar `delivered`, se requiere evidencia y firma.
Las rutas de guias requieren token Bearer.

`POST /api/v1/guides` ahora recibe `service_id` y `station_id`.
El backend toma el precio desde una regla activa de `pricing_rules`.

## Persistencia y migraciones

- La API ahora guarda guias y entregas en base de datos (no en memoria).
- En local, si `AUTO_CREATE_TABLES=true`, crea tablas al arrancar.
- Para staging/produccion use Alembic.

Comandos en `apps/api`:

```powershell
C:/Users/Lenovo/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -r requirements.txt
C:/Users/Lenovo/AppData/Local/Python/pythoncore-3.14-64/python.exe -m alembic upgrade head
```

Para crear una nueva migracion:

```powershell
C:/Users/Lenovo/AppData/Local/Python/pythoncore-3.14-64/python.exe -m alembic revision --autogenerate -m "mensaje"
```

## Cierre semanal automatico

Variables relevantes:

- `ENABLE_COMMISSION_SCHEDULER=true` activa scheduler interno.
- `COMMISSION_CLOSE_HOUR_UTC` y `COMMISSION_CLOSE_MINUTE_UTC` definen hora de ejecucion (lunes UTC).
- `COMMISSION_SCHEDULER_RUN_ON_STARTUP=true` ejecuta un cierre inmediato al arrancar API (usa semana previa).

Comando manual para cierre semanal (semana previa):

```powershell
C:/Users/Lenovo/AppData/Local/Python/pythoncore-3.14-64/python.exe -m app.scripts.close_commissions
```

Programar respaldo externo en Windows (Task Scheduler):

```powershell
Set-Location c:\Users\Lenovo\Documents\myproyect\mande24_independent
./scripts/register-weekly-close-task.ps1
```

Actualizar horario/configuracion de tarea:

```powershell
./scripts/update-weekly-close-task.ps1 -Hour 2 -Minute 30
```

Ejecutar tarea de inmediato (prueba):

```powershell
./scripts/run-weekly-close-task-now.ps1
```

Auditoria completa (health + cierre + validacion DB):

```powershell
./scripts/audit-weekly-close.ps1
```

Eliminar tarea:

```powershell
./scripts/unregister-weekly-close-task.ps1
```

Plantillas Linux `systemd`:

- `infra/systemd/mande24-weekly-commission-close.service`
- `infra/systemd/mande24-weekly-commission-close.timer`

## Siguiente fase recomendada

1. Persistencia real con SQLAlchemy + Alembic.
2. JWT + roles (`admin`, `station`, `rider`, `client`).
3. Carga de archivos en S3/MinIO.
4. Comisiones semanales y reportes PDF.
5. Pipeline CI/CD a staging y luego produccion.
