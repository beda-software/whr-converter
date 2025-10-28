"""
MedirecordsProprietaryClient - A client for interacting with the Medirecords API.

This client provides methods to interact with the Medirecords proprietary API,
including fetching appointments, patients, and other practice data.
"""

import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, date


class MedirecordsProprietaryClient:
    """
    Client for interacting with the Medirecords proprietary API.

    This client handles authentication and provides methods to access
    various endpoints of the Medirecords API.
    """

    def __init__(self, practice_id: str, access_token: Optional[str]):
        """
        Initialize the MedirecordsProprietaryClient.

        Args:
            practice_id: The practice ID for API calls
            access_token: API access token. If not provided, will use ACCESS_TOKEN env var
        """
        self.practice_id = practice_id
        self.access_token = access_token

        # Initialize requests session with authentication
        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.access_token})

        # Base API URL
        self.base_url = "https://api.medirecords.com/v1"

    def read(self, url: str) -> Dict[str, Any]:
        """
        Generic method to make GET requests to the API.

        Args:
            url: The API endpoint URL (relative to base URL)

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If the API request fails
        """
        full_url = f"{self.base_url}/{url}"
        response = self.session.get(full_url)
        response.raise_for_status()
        return response.json()

    def appointments(
        self, start_date: str, end_date: str, page: int = 0, size: int = 20
    ) -> Dict[str, Any]:
        """
        Get appointments for a specific date range with pagination.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            page: Page number (0-based)
            size: Number of items per page

        Returns:
            Dictionary containing paginated appointment data with metadata

        Example:
            client.appointments("2025-10-15", "2025-10-15", page=0, size=20)
        """
        url = f"practices/{self.practice_id}/appointments"
        params = {
            "appointmentDateRangeStart": f"{start_date}T00:00",
            "appointmentDateRangeEnd": f"{end_date}T23:59",
            "page": page,
            "size": size,
        }

        full_url = f"{self.base_url}/{url}"
        response = self.session.get(full_url, params=params)
        response.raise_for_status()
        return response.json()

    def get_appointments(
        self, start_date: str, end_date: str, page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all appointments for a specific date range, handling pagination automatically.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            page_size: Number of items per page (default: 20)

        Returns:
            List of all appointment data (flattened from all pages)

        Example:
            all_appointments = client.get_appointments("2025-10-15", "2025-10-15")
        """
        all_appointments = []
        page = 0

        while True:
            print(page, page_size)
            response = self.appointments(
                start_date, end_date, page=page, size=page_size
            )

            # Add appointments from current page
            all_appointments.extend(response.get("data", []))

            # Check if this is the last page
            if response.get("last", True):
                break

            page += 1

        return all_appointments

    def get_appointment_types(self) -> Dict[str, Any]:
        """
        Get available appointment types for the practice.

        Returns:
            Dictionary containing appointment types data
        """
        return self.read(f"practices/{self.practice_id}/appointment-types")

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient information by ID.

        Args:
            patient_id: The patient's unique identifier

        Returns:
            Dictionary containing patient data
        """
        return self.read(f"patients/{patient_id}")

    def get_practice_info(self) -> Dict[str, Any]:
        """
        Get practice information.

        Returns:
            Dictionary containing practice data
        """
        return self.read(f"practices/{self.practice_id}")

    def close(self):
        """
        Close the requests session.
        """
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
