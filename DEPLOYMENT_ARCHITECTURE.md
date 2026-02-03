

# 🚀 City Restaurants – Deployment Architecture (EC2 + Nginx + FastAPI + React)

## 1. Infrastructure Overview

This application is deployed on an **AWS EC2 Ubuntu instance** and consists of:

* **Frontend**: React (Vite build)
* **Backend**: FastAPI served via Gunicorn
* **Web Server / Reverse Proxy**: Nginx
* **Process Manager**: systemd
* **SSL**: Let’s Encrypt (Certbot)

All components run on **a single EC2 instance**, with Nginx acting as the entry point.

---

## 2. High-Level Request Flow

```text
Browser
  ↓
HTTPS (443)
  ↓
Nginx
  ├── Serves React static files
  └── Proxies /api & /auth requests
          ↓
      Gunicorn (FastAPI)
          ↓
        Database
```

---

## 3. Backend Deployment (FastAPI + Gunicorn)

### 3.1 Backend Service

The backend runs as a **systemd service**:

```bash
sudo systemctl status city_restaurants_backend.service
```

Service details:

* **Service name**: `city_restaurants_backend.service`
* **Process**: Gunicorn
* **Workers**: Multiple Gunicorn workers
* **Virtual environment**:

  ```
  /home/ubuntu/food/Development/Backend/city_restaurants_backend/.venv/
  ```

### 3.2 Gunicorn Command (Internally)

Gunicorn launches the FastAPI app:

```text
app.main:app
```

Gunicorn listens on:

```text
127.0.0.1:8000
```

> ⚠️ Gunicorn is **NOT exposed publicly**.
> It only accepts traffic from Nginx.

---

## 4. Frontend Deployment (React + Vite)

### 4.1 React Build Output

React is built using **Vite**, and the production build lives at:

```text
/home/ubuntu/food/Development/Frontend/city_restaurants_frontend/dist
```

This directory contains:

```text
index.html
/assets/
```

---

## 5. Nginx Configuration

Nginx is responsible for:

* SSL termination
* Serving React static files
* Reverse proxying API requests to FastAPI

### 5.1 Enabled Configuration

```text
/etc/nginx/sites-available/city_restaurants
```

Enabled via symlink in:

```text
/etc/nginx/sites-enabled/
```

---

## 6. HTTP → HTTPS Redirection

All HTTP traffic is redirected to HTTPS:

```nginx
server {
    listen 80;
    server_name indianrestros.com www.indianrestros.com;
    return 301 https://$host$request_uri;
}
```

✔ Ensures secure access
✔ Prevents mixed-content issues

---

## 7. HTTPS Server (Main Application)

### 7.1 SSL Configuration

Certificates are managed by **Certbot (Let’s Encrypt)**:

```text
/etc/letsencrypt/live/indianrestros.com/
```

Used by Nginx:

```nginx
ssl_certificate     fullchain.pem;
ssl_certificate_key privkey.pem;
```

---

## 8. React Static File Serving

Nginx serves the React app directly:

```nginx
root /home/ubuntu/food/Development/Frontend/city_restaurants_frontend/dist;
index index.html;
```

### 8.1 Static Assets Optimization

```nginx
location /assets/ {
    try_files $uri =404;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

✔ Long-term caching
✔ Better performance
✔ Smaller load times

---

## 9. API & Auth Reverse Proxy

### 9.1 `/api/*` Routes

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
}
```

### 9.2 `/auth/*` Routes

```nginx
location /auth/ {
    proxy_pass http://127.0.0.1:8000;
}
```

### 9.3 Headers Passed to Backend

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

✔ Correct client IP
✔ Correct protocol (HTTP/HTTPS)
✔ Required for CORS & security

---

## 10. React SPA Routing (Fallback)

For client-side routing (React Router):

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

✔ Prevents 404 on page refresh
✔ Enables deep links

---

## 11. Why This Architecture Works Well

✅ Backend isolated from public access
✅ Nginx handles SSL & performance
✅ React served as static files (fast)
✅ Clean separation of concerns
✅ Easy to scale backend workers

---

## 12. Common Maintenance Commands

### Restart backend

```bash
sudo systemctl restart city_restaurants_backend.service
```

### Restart nginx

```bash
sudo systemctl restart nginx
```

### Check logs

```bash
journalctl -u city_restaurants_backend.service -f
sudo tail -f /var/log/nginx/error.log
```

---

## 13. Summary

This deployment follows **industry best practices**:

* **Nginx** → Reverse proxy + SSL
* **Gunicorn** → Production-grade FastAPI server
* **React build** → Served as static assets
* **Systemd** → Reliable process management

It is **secure, scalable, and production-ready**.
