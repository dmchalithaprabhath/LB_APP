from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status

class LegislativeBoundaryAPITests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.valid_address = "620 N Harvey Ave, Oklahoma City, OK 73102, United States"
        self.invalid_address = "Invalid Address 12345"
        
        # Sample response from the geocoder for a valid address
        self.mock_geocode_response = {
            "latitude": 35.472,
            "longitude": -97.520
        }
        
        # Sample boundary data format for testing purposes
        self.mock_boundary_response = {
            "name": "Mock District",
            "polygon_coordinates": [
                [35.47, -97.52],
                [35.48, -97.53]
            ]
        }
        
    @patch('LB_API.views.geolocator.geocode')
    @patch('LB_API.views.fetch_boundary_data')
    def test_valid_address_with_boundary_data(self, mock_fetch_boundary_data, mock_geocode):
        # Mock the geocode and boundary data responses
        mock_geocode.return_value = type('Location', (object,), self.mock_geocode_response)
        mock_fetch_boundary_data.return_value = self.mock_boundary_response
        
        # Call the API with the valid address
        response = self.client.get(reverse('address_to_boundaries_view'), {'address': self.valid_address})
        
        # Check if the response structure matches the expected format
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify address and coordinates in response
        self.assertEqual(data['address'], self.valid_address)
        self.assertEqual(data['coordinates']['latitude'], self.mock_geocode_response['latitude'])
        self.assertEqual(data['coordinates']['longitude'], self.mock_geocode_response['longitude'])
        
        # Check if federal, state, and local boundary data are present
        self.assertIn("federal", data["legislative_boundaries"])
        self.assertIn("state", data["legislative_boundaries"])
        self.assertIn("local", data["legislative_boundaries"])
        
        # Verify the structure of one of the boundary items
        self.assertEqual(data["legislative_boundaries"]["federal"]["congressional_district"], self.mock_boundary_response)

    @patch('LB_API.views.geolocator.geocode')
    def test_invalid_address(self, mock_geocode):
        # Mock the geocode response for an invalid address
        mock_geocode.return_value = None
        
        # Call the API with the invalid address
        response = self.client.get(reverse('address_to_boundaries_view'), {'address': self.invalid_address})
        
        # Check if a 404 response is returned for an invalid address
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Address not found.")

    def test_missing_address_parameter(self):
        # Call the API without providing an address parameter
        response = self.client.get(reverse('address_to_boundaries_view'))
        
        # Check if a 400 response is returned when the address parameter is missing
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Address parameter is missing.")
