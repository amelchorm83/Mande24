# UAT - Contactos en Portales/PWA

Fecha: 2026-03-09
Release/Commit: c7dc1eb
Ambiente: local (http://localhost:3000 y http://localhost:8000)
Alcance: Alta y visualizacion de `Telefono fijo` y `WhatsApp` en cliente/estacion/repartidor, y presencia en detalle/impresion de guia.

## Evidencia automatizada ejecutada

- Script: `scripts/e2e_contact_fields_audit.ps1`
- Resultado: `PASS=27 WARN=0 FAIL=0`
- Cobertura: alta cliente, alta estacion, alta repartidor, creacion de guia, detalle de guia, guia imprimible/PDF con contactos.

- Script maestro: `scripts/e2e_audit_after_cleanup.ps1`
- Resultado: `PASS=103 WARN=0 FAIL=0`
- Cobertura adicional: smoke backend/web, negocio, negativos/permisos, exportes y extension de campos de contacto.

## Formato de Evidencia UAT (manual)

| ID | Caso | URL/Pantalla | Datos de prueba | Esperado | Obtenido | Estatus | Evidencia |
|---|---|---|---|---|---|---|---|
| UAT-01 | Ver campos en alta cliente | `/client` | N/A | Se muestran campos `Telefono fijo` y `WhatsApp` |  | Pendiente | Captura 1 |
| UAT-02 | Alta cliente con contactos | `/client` | Fijo: `9931001111`, WA: `529931001111` | Registro exitoso y guardado de ambos telefonos |  | Pendiente | Captura 2 |
| UAT-03 | Etiquetas con contacto en selectores | `/client` | Cliente creado en UAT-02 | Selectores muestran `Fijo` y `WhatsApp` en etiqueta |  | Pendiente | Captura 3 |
| UAT-04 | Ver campos en alta cliente desde estacion | `/station` -> Alta de Clientes | N/A | Se muestran `Telefono fijo` y `WhatsApp` |  | Pendiente | Captura 4 |
| UAT-05 | Alta cliente desde estacion y tabla | `/station` -> Alta de Clientes / Resultados | Fijo: `9931002222`, WA: `529931002222` | Se guarda y tabla muestra columnas `Telefono fijo` y `WhatsApp` |  | Pendiente | Captura 5 |
| UAT-06 | Alta repartidor con contactos | `/station` -> Alta de Repartidores | Fijo: `9931003333`, WA: `529931003333` | Registro exitoso y visible en `Catalogo de Repartidores` |  | Pendiente | Captura 6 |
| UAT-07 | Alta estacion con contactos | `/station` -> Alta de Estaciones | Fijo: `9931004444`, WA: `529931004444` | Registro exitoso y visible en `Catalogo de Estaciones` |  | Pendiente | Captura 7 |
| UAT-08 | Contactos en detalle de guia | `/ERPMande24/guides/{codigo}` | Guia nueva con entidades anteriores | Se ve bloque `Contactos Operativos` con `Telefono fijo` y `WhatsApp` |  | Pendiente | Captura 8 |
| UAT-09 | Contactos en impresion/PDF | `/ERPMande24/guides/{codigo}/print` | Misma guia UAT-08 | Vista imprimible muestra ambos telefonos |  | Pendiente | Captura 9 |
| UAT-10 | No regresion smoke portales | `/client`, `/station`, `/rider`, `/auth` | N/A | Responden HTTP 200 y sin error visible |  | Pendiente | Captura 10 |

## Criterio de aprobacion

- Minimo: 10/10 casos en `OK`.
- Sin bloqueadores P1/P2.
- Evidencias (capturas o video corto) adjuntas al ticket de liberacion.

## Aprobaciones

- QA: ____________________  Fecha: __________
- Operacion: ______________ Fecha: __________
- Producto: _______________ Fecha: __________
