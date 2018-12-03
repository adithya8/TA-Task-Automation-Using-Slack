from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import json


def get_service(api_name, api_version):
    """Get a service that communicates to a Google API.
    Args:
    api_name: The name of the api to connect to.
    api_version: The api version to connect to.
    scope: A list auth scopes to authorize for the application.
    key_file_location: The path to a valid service account p12 key file.
    service_account_email: The service account email address.
    Returns:
    A service that is connected to the specified API.
    """
    scope = ['https://www.googleapis.com/auth/drive',
             'https://www.googleapis.com/auth/calendar']

    # Define the auth scopes to request.
    # Use the developer console and replace the values with your
    # service account email and relative location of your key file.
    service_account_email = '<>'
    key_file_location = '<>'
    # Authenticate and construct service.
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        key_file_location, scope)
    http = credentials.authorize(httplib2.Http())
    # Build the service object.
    service = build(api_name, api_version, http=http)
    return service
