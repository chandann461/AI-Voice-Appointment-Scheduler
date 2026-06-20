# 🗓️ AI Voice Appointment Scheduler — Backend

A **FastAPI backend** for an AI voice assistant that books, reschedules, cancels, and looks up appointments. It's built to sit behind a voice platform (e.g. **Vapi**) as a set of callable tools/functions, and ships with a **Streamlit dashboard** for manually testing and managing the same data.

> This repo contains the API + admin dashboard + database layer. The voice-agent configuration (Vapi assistant, call flows, prompts) lives outside this repo and calls these endpoints as tools.

---

## 🚀 Key Features

- **Voice-assistant-ready REST API** — endpoints designed to be called as tool functions from a conversational AI agent
- Schedule, reschedule, cancel, list, and search appointments
- Conflict detection (no double-booking the same patient at the same time)
- Flexible datetime parsing (`YYYY-MM-DD HH:MM AM/PM`, 24-hour, with/without seconds)
- Persistent storage via SQLAlchemy (SQLite by default)
- Streamlit dashboard for manual booking, search, and cancellation — useful for testing without a live voice call
- Auto-generated interactive API docs (FastAPI `/docs`)

---

## 🧱 Tech Stack

| Layer            | Technology              |
|-------------------|--------------------------|
| API framework     | FastAPI + Uvicorn        |
| Voice integration | Vapi *(external to this repo — calls these endpoints as tools)* |
| Database / ORM    | SQLAlchemy (SQLite)      |
| Validation        | Pydantic v2               |
| Admin/test UI     | Streamlit                 |
| Language          | Python 3.12+              |

---

## 📂 Project Structure

```
.
├── backend.py        # FastAPI app — all appointment endpoints
├── table.py           # SQLAlchemy model, engine, and session setup
├── streamlit.py       # Streamlit dashboard for manual testing/management
├── mydb.db             # SQLite database file
├── pyproject.toml      # Project metadata & dependencies (uv)
├── uv.lock             # Locked dependency versions
└── requirements.txt    # Dependencies (pip alternative to uv)
```

---

## ⚙️ Setup

### 1. Install dependencies

Using `uv`:
```bash
uv sync
```

Or with `pip`:
```bash
pip install -r requirements.txt
```

> **Note:** `requirements.txt` includes `requests` and `pydantic` as explicit dependencies, but `pyproject.toml` / `uv.lock` currently don't list them. If you use `uv sync`, also run `uv add requests pydantic` (both are required — `requests` by the Streamlit dashboard, `pydantic` by the API models).

### 2. Run the API

```bash
python backend.py
```

This starts the FastAPI server at **`http://127.0.0.1:2000`**, and creates `mydb.db` automatically on first run if it doesn't exist. Interactive docs are available at `http://127.0.0.1:2000/docs`.

### 3. Run the dashboard (optional, for manual testing)

```bash
streamlit run streamlit.py
```

> ⚠️ **Known issue — port mismatch:** `streamlit.py` is currently hardcoded to call the API at `http://127.0.0.1:5000`, but `backend.py` runs on port `2000`. Update one of the two before running the dashboard — either change `API_BASE_URL` in `streamlit.py` to port `2000`, or run uvicorn on port `5000`.

> ⚠️ **Missing file:** `streamlit.py` imports helper functions from a `date_converter.py` module (for parsing flexible date formats like `15-05-2026` or `May 15, 2026`) that isn't included in this repo yet. The dashboard will fail to start without it.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health/info root |
| `GET`  | `/health` | Health check |
| `POST` | `/schedule_appointments/` | Book a new appointment |
| `POST` | `/cancel_appointment/` | Cancel by appointment ID, or by patient name + date |
| `GET`  | `/list_appointments/?date=YYYY-MM-DD` | List all active appointments for a given date |
| `GET`  | `/search_appointments/{patient_name}` | Find upcoming appointments for a patient |
| `PUT`  | `/reschedule_appointment/{appointment_id}?new_time=...` | Move an appointment to a new time |

All datetimes use the format `YYYY-MM-DD HH:MM AM/PM` (e.g. `2026-05-15 02:30 PM`).

---

## 🗺️ Roadmap

- [ ] Add `date_converter.py` (referenced by the dashboard but not yet included)
- [ ] Fix API port mismatch between `backend.py` and `streamlit.py`
- [ ] Wire up the Vapi voice assistant configuration and connect it to these endpoints
- [ ] Deploy to a cloud host (e.g. Render) and expose via a public webhook URL

---

## 📌 Status

Currently runs locally only — **not yet deployed**. The API is functional and ready to be wired up to a voice assistant; the next steps are fixing the issues above and standing up a public deployment for webhook access.
