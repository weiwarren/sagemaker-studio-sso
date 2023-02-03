import base64
import xml.etree.ElementTree as ET
import urllib.parse
import os
import boto3
import re
import time
# from aws_lambda_powertools import Logger


# logger = Logger(level="DEBUG")

# domainid field name (optional)
attr_domain_id =  os.environ.get('SAML_DOMAIN_FIELD', "domainid")

# saml username attribute to map to sagemaker profile name
attr_user_name = os.environ.get('SAML_USER_FIELD', "username")

def handler(event, context):
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

        for attribute in root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion").find("{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement").iter("{urn:oasis:names:tc:SAML:2.0:assertion}Attribute"):
            print("attr", attribute)
            if attribute.get('Name') == attr_domain_id:
                domain_id = attribute.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue").text
            elif attribute.get('Name') == attr_user_name:
                user_id = attribute.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue").text
        print(domain_id, user_id)

        # Validate that domain_id and user_id were extracted from the SAML response
        if domain_id is None:
            raise ValueError("Attribute 'domainid' not found in SAML response")
        if user_id is None:
            raise ValueError("attribute 'username' not found in SAML response")

            # Create a SageMaker client
        sagemaker = boto3.client('sagemaker')

        existing_user = None
        try:
             existing_user = sagemaker.describe_user_profile(DomainId=domain_id, UserProfileName=user_id)
        except:
            print(user_id, " does not exist. will provision it next ...")

        if existing_user is None:
            # Create a user profile
            sagemaker.create_user_profile(DomainId=domain_id, UserProfileName=user_id)

        existing_user = sagemaker.describe_user_profile(DomainId=domain_id, UserProfileName=user_id)
        
        # Create a presigned URL for the user
        url = sagemaker.create_presigned_domain_url(DomainId=domain_id, UserProfileName=user_id, ExpiresInSeconds=30)['AuthorizedUrl']

        # sagemaker presigned domain url is not immediately available to access after generated, added timer to avoid errors
        # browser refresh would fix this issue too
        time.sleep(5)

        # Return a redirect response to the presigned URL
        return {
            'statusCode': 302,
            'headers': {
                'Location': url
            },
            'body': ''
        }
    except ValueError as e:
        print(str(e))
        return {
            'statusCode': 400,
            'body': str(e)
        }
    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': str(e)
        }