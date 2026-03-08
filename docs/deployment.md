# Despliegue sugerido

## Ambientes

- Local: desarrollo y pruebas rapidas.
- Staging: validacion completa con dominio temporal.
- Produccion: trafico real.

## Requisitos minimos servidor

- Docker y Docker Compose
- 2 vCPU, 4 GB RAM (minimo)
- Dominio y SSL

## Flujo recomendado

1. Push a `main`.
2. CI ejecuta pruebas.
3. Despliegue automatico a staging.
4. Aprobacion manual.
5. Despliegue a produccion.

## Migraciones

Antes de levantar API en staging/produccion ejecute:

```powershell
python -m alembic upgrade head
```

## Cierre semanal de comisiones

Opcion A: active scheduler interno con `ENABLE_COMMISSION_SCHEDULER=true`.

Opcion B (manual por cron del servidor):

```powershell
python -m app.scripts.close_commissions
```

### Windows Task Scheduler

En servidor Windows puede registrar la tarea con:

```powershell
Set-Location C:\ruta\a\mande24_independent
.\scripts\register-weekly-close-task.ps1
```

Comandos utiles:

```powershell
.\scripts\update-weekly-close-task.ps1 -Hour 2 -Minute 30
.\scripts\run-weekly-close-task-now.ps1
.\scripts\unregister-weekly-close-task.ps1
.\scripts\audit-weekly-close.ps1
```

### Linux systemd timer

1. Copie:
- `infra/systemd/mande24-weekly-commission-close.service` a `/etc/systemd/system/`
- `infra/systemd/mande24-weekly-commission-close.timer` a `/etc/systemd/system/`
2. Active timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mande24-weekly-commission-close.timer
sudo systemctl status mande24-weekly-commission-close.timer
```

## Seguridad minima

- Cambiar secretos de `.env`.
- Activar HTTPS.
- Respaldos diarios de Postgres.
- Logs centralizados (Sentry/ELK/Cloud).
