# GitHub Setup Staging Smoke

Este checklist conecta el workflow `staging-smoke.yml` con tu repositorio en GitHub.

## 1) Subir cambios al repositorio
Asegurate de subir al menos:
- `.github/workflows/staging-smoke.yml`
- `scripts/health-smoke.ps1`
- `docs/OPERACION_DIARIA.md`

## 2) Crear environment `staging`
En GitHub:
1. Abre tu repositorio.
2. Ve a `Settings`.
3. Ve a `Environments`.
4. Click en `New environment`.
5. Nombre: `staging`.
6. Guardar.

## 3) Proteger environment con aprobacion
Dentro de `staging`:
1. En `Deployment protection rules`, activa `Required reviewers`.
2. Agrega al menos 1 reviewer.
3. (Opcional) configura `Wait timer`.
4. Guardar.

## 4) Crear secrets requeridos
En `Settings > Secrets and variables > Actions > New repository secret` crea:

- `STAGING_API_BASE`
  - Ejemplo: `https://api-staging.tudominio.com`
- `STAGING_WEB_BASE`
  - Ejemplo: `https://staging.tudominio.com`

## 5) Ejecutar smoke manual la primera vez
En `Actions`:
1. Abre workflow `Staging Smoke`.
2. Click `Run workflow`.
3. Si quieres solo health de endpoints, deja `run_guide_flow=false`.
4. Si quieres flujo funcional (crea guia), usa `run_guide_flow=true`.

## 6) Validar resultado
En la ejecución revisa:
- Job `smoke` en verde.
- Artifact `staging-health-smoke-report` descargable.

## 7) Comportamiento automatico
Despues de esto, el workflow se puede ejecutar automaticamente tras `API Tests` y `Web Build` exitosos en `main`, respetando aprobaciones del environment `staging`.
