import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- CONFIGURATION ---
DW_API_KEY = os.getenv("DW_API_KEY")
DW_API_URL = "https://api.datawrapper.de/v3/charts"


# --- HELPER FUNCTIONS ---

def create_dw_chart(headers: dict, title: str) -> str:
    # ... (no changes needed)
    print("Step 1: Creating a new chart in Datawrapper...")
    payload = {"title": title, "type": "tables"}
    response = requests.post(DW_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    chart_id = response.json()["id"]
    print(f"  > Success! Chart created with ID: {chart_id}")
    return chart_id


def upload_data_to_dw_chart(headers: dict, chart_id: str, data: pd.DataFrame):
    # ... (no changes needed)
    print(f"Step 2: Uploading data to chart {chart_id}...")
    csv_data = data.to_csv(index=False)
    data_headers = {"Authorization": headers["Authorization"], "Content-Type": "text/csv"}
    response = requests.put(f"{DW_API_URL}/{chart_id}/data", headers=data_headers, data=csv_data.encode('utf-8'))
    response.raise_for_status()
    print("  > Success! Data uploaded.")


def update_dw_chart_metadata(headers: dict, chart_id: str, metadata: dict):
    # ... (no changes needed)
    print(f"Step 3: Updating chart metadata...")
    response = requests.patch(f"{DW_API_URL}/{chart_id}", headers=headers, json=metadata)
    response.raise_for_status()
    print("  > Success! Metadata updated.")


def publish_dw_chart(headers: dict, chart_id: str) -> dict:
    # ... (no changes needed)
    print(f"Step 4: Publishing chart {chart_id}...")
    response = requests.post(f"{DW_API_URL}/{chart_id}/publish", headers=headers)
    response.raise_for_status()
    print("  > Success! Chart has been published.")
    return response.json()


def download_chart_image(headers: dict, chart_id: str, file_name: str):
    """
    Downloads a published chart as a PNG image.
    """
    print(f"Step 5: Downloading chart {chart_id} as a PNG...")
    export_params = {"unit": "px", "mode": "rgb", "width": 600, "plain": "false", "borderWidth": 10}
    export_url = f"https://api.datawrapper.de/v3/charts/{chart_id}/export/png"
    response = requests.get(export_url, headers=headers, params=export_params)
    response.raise_for_status()
    with open(file_name, 'wb') as f:
        f.write(response.content)
    print(f"  > Success! Image saved to '{file_name}'")


# --- MAIN WORKFLOW FUNCTION ---

def create_datawrapper_from_df(team_losses_df: pd.DataFrame, output_image_name: str):
    """
    Takes a DataFrame and runs the full workflow to create, publish,
    and download a Datawrapper table.
    """
    if not DW_API_KEY:
        print("ERROR: Datawrapper API key not found.")
        return

    print("--- Starting Datawrapper API Workflow ---")

    # FIX 1: Define metadata with number formatting
    chart_title = "Projected Wins Lost Due to Injury (2024-25)"
    chart_metadata = {
        "metadata": {
            "describe": {
                "intro": "This table shows the estimated number of marginal wins each team is projected to lose due to player injuries over the 2024-25 season.",
                "byline": "Your Name / Your Team",
                "source-name": "Internal Model (Basketball-Reference)",
                "source-url": "https://www.basketball-reference.com/"
            },
            "visualize": {
                "table-columns": {
                    "wins_lost": {"barChart": True, "barColor": "#c52222", "number-format": "0.00"}
                }
            }
        }
    }

    auth_headers = {"Authorization": f"Bearer {DW_API_KEY}"}

    try:
        chart_id = create_dw_chart(auth_headers, chart_title)
        upload_data_to_dw_chart(auth_headers, chart_id, team_losses_df)
        update_dw_chart_metadata(auth_headers, chart_id, chart_metadata)
        publish_info = publish_dw_chart(auth_headers, chart_id)

        # NEW: Call the function to download the image
        download_chart_image(auth_headers, chart_id, output_image_name)

        print("\n--- FINAL OUTPUT ---")
        public_url = publish_info["data"]["publicUrl"]
        print(f"\nPublic URL: {public_url}")

    except requests.exceptions.HTTPError as e:
        print(f"\nAN API ERROR OCCURRED: Status Code: {e.response.status_code}, Response: {e.response.text}")


# --- SCRIPT ENTRY POINT ---

if __name__ == "__main__":
    csv_file_path = "wins_lost_to_injury_2024-2025.csv"
    output_png_path = "wins_lost_table.png"

    if not os.path.exists(csv_file_path):
        print(f"ERROR: Input file not found at '{csv_file_path}'")
    else:
        print(f"Loading data from '{csv_file_path}'...")
        final_team_losses = pd.read_csv(csv_file_path)
        create_datawrapper_from_df(final_team_losses, output_png_path)