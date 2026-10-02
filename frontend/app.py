"""Streamlit operator dashboard for Foobar Transport Control."""

import os

import requests
import streamlit as st

API_URL = os.getenv("FOOBAR_API_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 3

st.set_page_config(page_title="Foobar Transport Control", page_icon="🚀", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .vehicle-route { color: #536579; font-size: 1.02rem; margin: .2rem 0 .75rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Foobar Transport Control")
st.caption("Transportation Operations — Star A ↔ Star B")


def load_vehicles() -> list[dict]:
    """Read the current vehicle list, showing a useful error if the API is down."""
    try:
        response = requests.get(f"{API_URL}/vehicles", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(
            "Could not connect to the transport API. Start the FastAPI server and "
            f"refresh this page. ({exc})"
        )
        st.stop()


def send_action(vehicle_id: str, action: str) -> None:
    """Send a control request and report API or connection errors."""
    try:
        response = requests.post(
            f"{API_URL}/vehicles/{vehicle_id}/{action}", timeout=REQUEST_TIMEOUT_SECONDS
        )
        if response.ok:
            st.rerun()
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        st.error(f"The API could not {action} {vehicle_id}: {detail}")
    except requests.RequestException as exc:
        st.error(f"Could not reach the transport API: {exc}")


vehicles = load_vehicles()
available_count = sum(vehicle["status"] == "available" for vehicle in vehicles)
in_transit_count = sum(vehicle["status"] == "in_transit" for vehicle in vehicles)
total_foobar = sum(vehicle["foobar_quantity"] for vehicle in vehicles)

metric_columns = st.columns(4)
metric_columns[0].metric("Total Vehicles", len(vehicles))
metric_columns[1].metric("Available", available_count)
metric_columns[2].metric("In Transit", in_transit_count)
metric_columns[3].metric("Total Foobar", f"{total_foobar:,}")

st.divider()
st.subheader("Fleet overview")

for row_start in range(0, len(vehicles), 3):
    columns = st.columns(3)
    for column, vehicle in zip(columns, vehicles[row_start : row_start + 3]):
        with column:
            with st.container(border=True):
                st.markdown(f"### {vehicle['id']}")
                st.markdown(
                    f"<div class='vehicle-route'>{vehicle['origin']} &nbsp;→&nbsp; "
                    f"{vehicle['destination']}</div>",
                    unsafe_allow_html=True,
                )

                if vehicle["status"] == "available":
                    st.success("Available", icon="✅")
                elif vehicle["status"] == "in_transit":
                    st.warning("In Transit", icon="🚀")
                elif vehicle["status"] == "completed":
                    st.info("Completed", icon="🏁")
                else:
                    st.error("Cancelled", icon="⛔")

                st.write(f"**Foobar quantity:** {vehicle['foobar_quantity']:,}")
                if vehicle["status"] == "available":
                    st.button(
                        "Start Crossing",
                        key=f"start-{vehicle['id']}",
                        type="primary",
                        use_container_width=True,
                        on_click=send_action,
                        args=(vehicle["id"], "start"),
                    )
                elif vehicle["status"] == "in_transit":
                    st.button(
                        "Cancel Crossing",
                        key=f"cancel-{vehicle['id']}",
                        use_container_width=True,
                        on_click=send_action,
                        args=(vehicle["id"], "cancel"),
                    )
