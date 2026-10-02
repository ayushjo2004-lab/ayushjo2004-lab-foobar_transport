"""Small in-memory API for monitoring and controlling foobar crossings."""

from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

VehicleStatus = Literal["available", "in_transit", "completed", "cancelled"]


class Vehicle(BaseModel):
    id: str
    origin: Literal["Star A", "Star B"]
    destination: Literal["Star A", "Star B"]
    status: VehicleStatus
    foobar_quantity: int = Field(ge=0)


class HealthResponse(BaseModel):
    status: Literal["ok"]


app = FastAPI(title="Foobar Transport Control API", version="1.0.0")

# The data intentionally lives only in memory and resets when the API restarts.
_vehicles: dict[str, Vehicle] = {
    "V-001": Vehicle(
        id="V-001", origin="Star A", destination="Star B", status="available", foobar_quantity=120
    ),
    "V-002": Vehicle(
        id="V-002", origin="Star B", destination="Star A", status="available", foobar_quantity=85
    ),
    "V-003": Vehicle(
        id="V-003", origin="Star A", destination="Star B", status="available", foobar_quantity=200
    ),
}
_vehicles_lock = Lock()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/vehicles", response_model=list[Vehicle])
def get_vehicles() -> list[Vehicle]:
    with _vehicles_lock:
        # Return independent model instances so callers cannot mutate stored state.
        return [vehicle.model_copy(deep=True) for vehicle in _vehicles.values()]


@app.post("/vehicles/{vehicle_id}/start", response_model=Vehicle)
def start_crossing(vehicle_id: str) -> Vehicle:
    with _vehicles_lock:
        vehicle = _vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if vehicle.status == "in_transit":
            raise HTTPException(status_code=409, detail="Vehicle is already in transit")

        updated = vehicle.model_copy(update={"status": "in_transit"})
        _vehicles[vehicle_id] = updated
        return updated


@app.post("/vehicles/{vehicle_id}/cancel", response_model=Vehicle)
def cancel_crossing(vehicle_id: str) -> Vehicle:
    with _vehicles_lock:
        vehicle = _vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        if vehicle.status != "in_transit":
            raise HTTPException(status_code=409, detail="Vehicle is not currently in transit")

        updated = vehicle.model_copy(update={"status": "cancelled"})
        _vehicles[vehicle_id] = updated
        return updated
