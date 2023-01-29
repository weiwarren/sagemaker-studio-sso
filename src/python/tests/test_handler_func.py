import unittest
import urllib.parse
import base64
import re
import xml.etree.ElementTree as ET
import boto3
from mock import MagicMock, patch

class TestLambdaHandler(unittest.TestCase):

    def setUp(self):
        self.event = {'body': 'base64encodedstring'}
        self.context = {}

    @patch('boto3.client')
    def test_valid_saml_response(self, mock_boto3):
        # Create a mock response for the describe_user_profile method
        mock_response = {'UserProfile': {'DomainId': 'd-1234567890', 'UserProfileName': 'testuser'}}
        mock_boto3.return_value.describe_user_profile.return_value = mock_response

        # Call the lambda_handler function with a valid SAML response
        response = lambda_handler(self.event, self.context)

        # Assert that the function returned a redirect response
        self.assertEqual(response['statusCode'], 302)
        self.assertEqual(response['headers']['Location'], 'http://example.com/presigned_url')
        self.assertEqual(response['body'], '')

    @patch('boto3.client')
    def test_saml_response_missing_attributes(self, mock_boto3):
        # Create a mock response for the describe_user_profile method
        mock_response = {'UserProfile': {'DomainId': '', 'UserProfileName': ''}}
        mock_boto3.return_value.describe_user_profile.return_value = mock_response

        # Call the lambda_handler function with a SAML response missing attributes
        response = lambda_handler(self.event, self.context)

        # Assert that the function returned a bad request response
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], "attribute 'domainid' not found in SAML response")

    @patch('boto3.client')
    def test_saml_response_error(self, mock_boto3):
        # Create a mock response for the describe_user_profile method
        mock_response = {'UserProfile': {'DomainId': 'd-1234567890', 'UserProfileName': 'testuser'}}
        mock_boto3.return_value.describe_user_profile.return_value = mock_response

        # Call the lambda_handler function with an event that will cause an exception
        self.event = {'body': 'invalidbase64encodedstring'}
        response = lambda_handler(self.event, self.context)

        # Assert that the function returned a server error response
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], "Incorrect padding")

