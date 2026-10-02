# Foobar Transport Control

A small transportation monitoring and control assessment project for moving foobar between Star A and Star B.

## Assumptions

- Star A and Star B are the only endpoints, and each vehicle has a fixed direction.
- The fleet contains V-001, V-002, and V-003. Each has a fixed foobar quantity.
- All vehicles start as `available` when the backend starts.
- A vehicle cannot start another crossing while its status is `in_transit`.
- Cancelling an active crossing sets its status to `cancelled`. The dashboard offers Start Crossing for available vehicles and Cancel Crossing for in-transit vehicles.
- `completed` is part of the status model for future extension; this small assessment does not simulate arrival or expose a completion endpoint.
- Data is held in backend memory and resets to the initial fleet if the backend restarts. No database or authentication is used.

## Architecture

- **FastAPI backend:** owns the vehicle state and validates every state-changing request. A lock protects the in-memory check-and-update operation, including simultaneous requests.
- **Streamlit frontend:** reads the fleet from the API, calculates the dashboard metrics, and sends start/cancel requests with `requests`.
- **In-memory storage:** a Python dictionary keeps the implementation easy to inspect; it is intentionally not durable.

## Safety rule

The backend is authoritative. The start endpoint checks the stored status while holding a lock and returns HTTP `409 Conflict` if the vehicle is already in transit. Hiding or repeating a dashboard button cannot bypass this check. Cancel also requires the vehicle to be in transit.

## API contract

All successful responses use JSON. Error responses include a `detail` message.

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| `GET` | `/health` | `200`, `{"status":"ok"}` | — |
| `GET` | `/vehicles` | `200`, array of vehicle objects | — |
| `POST` | `/vehicles/{vehicle_id}/start` | `200`, updated vehicle with `in_transit` status | `404` unknown vehicle; `409` already in transit |
| `POST` | `/vehicles/{vehicle_id}/cancel` | `200`, updated vehicle with `cancelled` status | `404` unknown vehicle; `409` not currently in transit |

Vehicle objects have `id`, `origin`, `destination`, `status`, and non-negative integer `foobar_quantity` fields. Status is one of `available`, `in_transit`, `completed`, or `cancelled`.

## Project structure

```text
foobar_transport/
├── backend/
│   ├── __init__.py
│   └── main.py
├── frontend/
│   └── app.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Run on Windows with VS Code

Use Python 3.9 or newer.

1. Open the `foobar_transport` folder in VS Code.
2. Open a terminal in VS Code and create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. In that terminal, start FastAPI:

   ```powershell
   uvicorn backend.main:app --reload
   ```

4. Open a second VS Code terminal in the same `foobar_transport` folder. Activate the environment there and start Streamlit:

   ```powershell
   .venv\Scripts\activate
   streamlit run frontend/app.py
   ```

5. Open the local Streamlit URL printed in the terminal (usually `http://localhost:8501`). FastAPI's interactive Swagger docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

If the API runs on another address, set `FOOBAR_API_URL` in the environment before starting Streamlit, for example `$env:FOOBAR_API_URL = "http://127.0.0.1:8000"` in PowerShell.

## Run the end-to-end check

The end-to-end test talks to a running API. Start the backend in one terminal from this folder:

```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, run:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The test starts the first available vehicle and leaves it `in_transit` in the API's in-memory state. Restart the backend to restore the initial fleet. The dashboard can be run separately with `streamlit run frontend/app.py`.

## Manual checks

- Load the dashboard and confirm it shows 3 vehicles, 3 available, 0 in transit, and 405 total foobar.
- Start a vehicle. Confirm its status becomes In Transit and the in-transit metric increments.
- Try starting that same vehicle again in Swagger. Confirm the API returns `409`.
- Cancel the active crossing. Confirm the status becomes Cancelled and it is no longer counted as in transit.
- Try cancelling that vehicle again in Swagger and use an unknown vehicle ID for start/cancel. Confirm each request returns `409` or `404` as appropriate.
- Stop and restart FastAPI. Confirm the in-memory fleet returns to its initial state.
- Stop FastAPI and refresh the dashboard. Confirm it shows a readable connection error.
