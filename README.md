# Mis Gastos — app nativa (PWA) con sincronización

App offline-first para anotar gastos e ingresos. Guarda en el teléfono
(IndexedDB) y sincroniza con tu servidor cuando hay internet. Se instala
como app con ícono propio.

## Qué hay aquí
- `web/` — la app (PWA): `index.html`, `sw.js`, `manifest.webmanifest`, íconos.
- `server/` — backend de sync: `main.py` (FastAPI + SQLite), `requirements.txt`.
- `deploy/` — `gastos.nginx.conf` (vhost) y `gastos.service` (systemd).

> El iPhone necesita **HTTPS** para instalar la PWA y para el service worker.
> El VPS ya corre **nginx**, así que servimos detrás de él y sacamos el
> certificado con **certbot**. Con `sslip.io` no hace falta registrar dominio.

---

## Deploy automático (puente GitHub → VPS)
Como en ISP-System: cada `push` a `main` dispara el workflow
`.github/workflows/deploy.yml`, que copia `web/` y `server/` al VPS
(`/opt/gastos`) y reinicia el servicio `gastos`.

Requiere dos secrets en el repo (`Settings → Secrets → Actions`):
- `VPS_HOST` = `5.161.239.156`
- `VPS_SSH_KEY` = clave SSH privada con acceso root al VPS

Monitor: https://github.com/emanueld92/MisGastosapp/actions

## Infra en el VPS (una sola vez)
- Backend FastAPI en `127.0.0.1:8010` vía systemd (`deploy/gastos.service`).
  El puerto 8000 ya lo usa ISP-System.
- nginx sirve `gastos.5.161.239.156.sslip.io`: estático desde `/opt/gastos/web`
  y `/api/*` → `127.0.0.1:8010` (`deploy/gastos.nginx.conf`).
- TLS con `certbot --nginx`.
- Token de la API en `GASTOS_TOKEN` dentro de `/etc/systemd/system/gastos.service`
  (generado con `openssl rand -hex 24`, **no** vive en el repo).

Abre `https://gastos.5.161.239.156.sslip.io`.

> ¿Dominio propio? Apunta un registro A a `5.161.239.156`, cambia `server_name`
> en el vhost y vuelve a correr `certbot --nginx`.

## 4. Instalar en el iPhone
1. Abre la URL en **Safari**.
2. Toca **Compartir** → **Añadir a pantalla de inicio**.
3. Ábrela desde el ícono nuevo: arranca a pantalla completa, como app.
4. En la app: sección **Sincronización** → deja *Servidor* vacío (usa el mismo
   dominio) y pega el **mismo token** del paso 2 → **Guardar**.

Listo. Anota offline; cuando haya internet se sincroniza solo (al abrir, al
recuperar señal y tras cada cambio). El punto verde arriba indica "al día".

## Notas
- **Respaldo extra:** el botón *Exportar a Excel* genera un .xlsx real; en el
  iPhone el menú de compartir te deja "Guardar en Drive".
- **Seguridad:** el token protege la API. Mantén la URL privada. Si quieres más,
  puedes exponer el servicio solo por la red WireGuard.
- **Varios dispositivos:** instala igual en otro teléfono/PC con el mismo token
  y comparten los mismos datos.
