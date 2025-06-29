# WarenWelt

WarenWelt ist ein Warenwirtschaftssystem für SecondHand Shops, das Regalvermietung und Kleider-Basare unterstützt. Es wird mit Vue.js im Frontend und einer Python/FastAPI REST-API im Backend entwickelt.

## Features (MVP)

*   Lieferantenverwaltung
*   Artikelverwaltung (Kommission & Neuware)
*   Produktkategorien
*   Steuersätze
*   Verkaufsabwicklung (Kasse)
*   Auszahlungen an Lieferanten (vereinfacht)
*   Benutzerverwaltung (Admin, Mitarbeiter) mit JWT-Authentifizierung

## Features (Phase 2)

Die folgenden Funktionen wurden in Phase 2 hinzugefügt oder erweitert:

*   **Regalvermietungssystem:**
    *   Verwaltung von Regalen/Flächen (Erstellen, Anzeigen, Bearbeiten, Löschen).
    *   Verwaltung von Mietverträgen für Lieferanten (Laufzeit, Preis, Status).
    *   Automatische (simulierte) monatliche Rechnungsstellung für die Miete (Backend-Logik vorhanden, Generierung per API-Aufruf).
    *   *Hinweis: Vertragsausdruck und grafische Regalübersicht sind noch nicht implementiert.*
*   **Reporting & Buchhaltung:**
    *   Tages-, Wochen- und Monatslosungen (Verkaufszusammenfassungen).
    *   Detaillierte Umsatzlisten mit Ausweisung von Neuware und Kommissionsware.
    *   CSV-Export für Tages- und Monatslosungen.
    *   CSV-Export für Umsatzlisten in einem vereinfachten "DATEV-ähnlichen" Format.
    *   *Hinweis: Die genaue Implementierung der Differenzbesteuerung im Reporting und Export steht noch aus und erfordert buchhalterische Spezifikationen.*
*   **Lieferanten-Kommunikation:**
    *   Automatisierter E-Mail-Versand für Auszahlungsbenachrichtigungen an Lieferanten (SMTP-Server muss konfiguriert sein).
*   **Daten-Import:**
    *   Import von Artikellisten (Produkten) per CSV.
    *   Import von Lieferanten per CSV.

## Technologie-Stack

*   **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Uvicorn
*   **Frontend:** Vue.js (Vue 3), Vue Router, Pinia, Axios, Vite
*   **Datenbank (MVP):** SQLite
*   **Containerisierung:** Docker, Docker Compose

## Voraussetzungen

*   Docker (https://www.docker.com/get-started)
*   Docker Compose (wird normalerweise mit Docker Desktop installiert)

## Setup und Start mit Docker Compose

1.  **Repository klonen (falls noch nicht geschehen):**
    ```bash
    git clone [<repository-url>](https://github.com/stiegler-it/WarenWelt.git)
    cd warenwelt # Oder wie das Root-Verzeichnis heißt
    ```

2.  **Umgebungsvariablen konfigurieren:**
    Kopieren Sie die Datei `.env.example` zu `.env` im Projekt-Root-Verzeichnis:
    ```bash
    cp .env.example .env
    ```
    Öffnen Sie die `.env`-Datei und passen Sie die Variablen bei Bedarf an. **Wichtig:** Generieren Sie einen neuen `SECRET_KEY` für eine Produktivumgebung!
    ```dotenv
    # .env (Beispiel)
    SECRET_KEY="IhrGenerierterSuperGeheimerSchlüsselHier"
    DATABASE_URL="sqlite:///data/test.db"
    VITE_FRONTEND_API_BASE_URL="http://api:8000/api/v1"
    ```

3.  **Anwendung starten:**
    Führen Sie den folgenden Befehl im Projekt-Root-Verzeichnis aus (wo sich die `docker-compose.yml` befindet):
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: Erstellt die Docker-Images neu, falls sie noch nicht existieren oder Änderungen in den Dockerfiles/Code vorgenommen wurden.
    *   `-d`: Startet die Container im Hintergrund (detached mode).

4.  **Anwendung ist bereit:**
    *   Das **Frontend** sollte unter `http://localhost:8080` erreichbar sein.
    *   Das **Backend API** ist unter `http://localhost:8000` erreichbar (Swagger UI Docs unter `http://localhost:8000/docs`).

5.  **Datenbankmigrationen (Backend):**
    Das Backend führt beim Start automatisch die Datenbankmigrationen (Alembic) aus, um die Datenbankstruktur zu erstellen oder zu aktualisieren. Die SQLite-Datenbankdatei (`test.db`) wird im Docker-Volume `backend_data` gespeichert und bleibt somit auch nach dem Stoppen der Container erhalten.

6.  **Initialer Admin-Benutzer (Hinweis):**
    Für das MVP gibt es noch keine automatische Erstellung eines Admin-Benutzers über die API oder einen Seed-Mechanismus im Docker-Setup. Dies müsste manuell in der Datenbank erfolgen oder durch eine Erweiterung des Entrypoint-Skripts/Alembic-Migration (Beispiele dafür sind in den Backend-Kommentaren zu finden).
    *   Mögliche Standard-Admin-Daten (falls manuell oder per Seed erstellt):
        *   E-Mail: `admin@warenwelt.test` (oder `admin@example.com`)
        *   Passwort: `adminpass` (**unbedingt ändern!**)

## Stoppen der Anwendung

Um die Anwendung zu stoppen:
```bash
docker-compose down
```
Wenn Sie auch die Docker-Volumes entfernen möchten (Vorsicht: Dies löscht die Datenbankdaten!):
```bash
docker-compose down -v
```

## Entwicklung

### Backend (FastAPI)
Das Backend befindet sich im Ordner `warenwelt-backend`.

### Frontend (Vue.js)
Das Frontend befindet sich im Ordner `warenwelt-frontend`.

---
*Dieses README wird im Laufe der Entwicklung erweitert.*
