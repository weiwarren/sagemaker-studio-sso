import base64
import xml.etree.ElementTree as ET
import urllib.parse
import boto3
import re
import time
# from aws_lambda_powertools import Logger


# logger = Logger(level="DEBUG")

def lambda_handler(event, context):
    try:
        # Decode and parse the SAML response
        response = urllib.parse.unquote(base64.b64decode(event['body']).decode('ascii'))
        match = re.search(r'samlresponse=([^&]+)', response,  re.IGNORECASE)
        if match: saml_token = match.group(1)
        saml_xml = base64.b64decode(saml_token)
        root = ET.fromstring(saml_xml)
        # logger.debug(root)
        
        # Extract the domainid and username attributes
        domain_id = None
        user_id = None
        # logger.debug(root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion").find("{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement"))
        for attribute in root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion").find("{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement").iter("{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"):
            print("attr", attribute)
            if attribute.get('Name') == 'domainid':
                domain_id = attribute.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue").text
            elif attribute.get('Name') == 'username':
                user_id = attribute.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue").text

        # Validate that domain_id and user_id were extracted from the SAML response
        if domain_id is None:
            raise ValueError("Attribute 'domainid' not found in SAML response")
        if user_id is None:
            raise ValueError("attribute 'username' not found in SAML response")

            # Create a SageMaker client
        sagemaker = boto3.client('sagemaker')

        existing_user = sagemaker.describe_user_profile(DomainId=domain_id, UserProfileName=user_id)

        if existing_user is None:
            # Create a user profile
            sagemaker.create_user_profile(DomainId=domain_id, UserProfileName=user_id)
   
        # Create a presigned URL for the user
        # todo: cache the url for future
        url = sagemaker.create_presigned_domain_url(DomainId=domain_id, UserProfileName=user_id, ExpiresInSeconds=5)['AuthorizedUrl']
        # if the url is generated for the first time, there is a slight delay before it is accessible
        # otherwise there will be error on user-profile [userprofile] is not in InService
        # there is no api to check whether it is accessible or not
        # introducing timer here, can be improved with caching
        time.sleep(3)
        # Return a redirect response to the presigned URL
        return {
            'statusCode': 302,
            'headers': {
                'Location': url
            },
            'body': ''
        }
    except ValueError as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }