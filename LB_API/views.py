from django.http import JsonResponse
from geopy.geocoders import Nominatim
import requests
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

# Initialize the geolocator
geolocator = Nominatim(user_agent="DjangoLegislativeBoundaryAPI/1.0 (dmchalitha@gmail.com)")

# Organize datasets by federal, state, and local
DATASET_URLS = {
    'federal': {
        'congressional_district': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0',
    },
    'state': {
        'state_senate_district': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/1',
        'state_house_district': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/2',
        'state_boundaries': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/0',
    },
    'local': {
        'county_boundaries': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1',
        'municipal_boundaries': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/1',
        'city_boundaries': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4',
        'unified_school_district': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0'
    }
}

# Helper function to fetch boundary data for a dataset
def fetch_boundary_data(latitude, longitude, dataset_url):
    query_url = f"{dataset_url}/query?geometry={longitude},{latitude}&geometryType=esriGeometryPoint&inSR=4326&outFields=*&returnGeometry=true&f=json"
    response = requests.get(query_url).json()
    
    if "features" in response and response["features"]:
        feature = response["features"][0]
        name = feature["attributes"].get("NAME", "Unknown")
        polygon_coordinates = []
        
        # Extract polygon coordinates if available
        if "geometry" in feature and "rings" in feature["geometry"]:
            for ring in feature["geometry"]["rings"]:
                polygon_coordinates.append([[round(coord[1], 6), round(coord[0], 6)] for coord in ring])

        return {
            "name": name,
            "polygon_coordinates": polygon_coordinates
        }
    return None

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('address', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Address to geocode")],
    responses={200: "Sample JSON output with legislative boundaries data"}
)
@api_view(['GET'])
def address_to_boundaries_view(request):
    address = request.GET.get('address')
    if not address:
        return JsonResponse({"error": "Address parameter is missing."}, status=400)

    # Geocode the address to get latitude and longitude
    location = geolocator.geocode(address)
    if not location:
        return JsonResponse({"error": "Address not found."}, status=404)

    # Prepare the response structure
    response_data = {
        "address": address,
        "coordinates": {
            "latitude": location.latitude,
            "longitude": location.longitude
        },
        "legislative_boundaries": {
            "federal": {},
            "state": {},
            "local": {}
        }
    }

    # Fetch boundary data for each category
    for category, datasets in DATASET_URLS.items():
        for dataset_name, dataset_url in datasets.items():
            boundary_data = fetch_boundary_data(location.latitude, location.longitude, dataset_url)
            if boundary_data:
                response_data["legislative_boundaries"][category][dataset_name] = boundary_data

    return JsonResponse(response_data, json_dumps_params={'indent': 2})
