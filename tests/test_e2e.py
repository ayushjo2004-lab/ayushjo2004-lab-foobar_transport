"""End-to-end check against the live Foobar Transport API."""

import unittest

import requests


BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 5


class VehicleMonitoringEndToEndTest(unittest.TestCase):
    def api_request(self, method: str, path: str) -> requests.Response:
        print(f"{method} {BASE_URL}{path}", flush=True)
        try:
            return requests.request(
                method, f"{BASE_URL}{path}", timeout=TIMEOUT_SECONDS
            )
        except requests.RequestException as exc:
            self.fail(f"FAIL: {method} {path} could not reach the live API: {exc}")

    def test_start_crossing_updates_monitoring_response(self) -> None:
        monitoring_response = self.api_request("GET", "/vehicles")
        self.assertEqual(monitoring_response.status_code, 200)
        vehicles = monitoring_response.json()
        available_vehicle = next(
            (vehicle for vehicle in vehicles if vehicle["status"] == "available"), None
        )
        self.assertIsNotNone(available_vehicle, "No available vehicle was returned")

        vehicle_id = available_vehicle["id"]
        self.assertTrue(any(vehicle["id"] == vehicle_id for vehicle in vehicles))
        print(f"PASS: {vehicle_id} appears in the monitoring response as available", flush=True)

        start_response = self.api_request("POST", f"/vehicles/{vehicle_id}/start")
        self.assertEqual(start_response.status_code, 200, start_response.text)
        self.assertEqual(start_response.json()["status"], "in_transit")
        print(f"PASS: start response status is in_transit for {vehicle_id}", flush=True)

        updated_response = self.api_request("GET", "/vehicles")
        self.assertEqual(updated_response.status_code, 200)
        updated_vehicles = updated_response.json()
        updated_vehicle = next(
            (vehicle for vehicle in updated_vehicles if vehicle["id"] == vehicle_id), None
        )
        self.assertIsNotNone(updated_vehicle, f"{vehicle_id} disappeared from monitoring")
        self.assertEqual(updated_vehicle["status"], "in_transit")
        print(
            f"PASS: monitoring response shows {vehicle_id} as in_transit",
            flush=True,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
