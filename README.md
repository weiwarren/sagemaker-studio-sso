# Sagemaker Studio Single Sign-On Automation

This repository contains the code for automating the single sign-on process for Sagemaker Studio using Terraform and a Lambda function.

![alt text](https://github.com/weiwarren/sagemaker-studio-sso/blob/master/architecture.png?raw=true)


```
AWS SSO => IDP (tested against Okta, auth0, and AWS SSO) => API Gateway => Lambda => Sagemaker Studio nodebook
```
User authenticate throug to AWS SSO dashboard, clicking the saml 2.0 custom icon will trigger request to lambda function via API gateway to check and provision user profile associated with the configured field. Then function then generates a presigned url, before sending 302 redirect with the url to the user.

## Terraform Code
The Terraform code in this repository is used to deploy an API Gateway and a Lambda function to handle the single sign-on process. The API Gateway is configured to accept a username as a parameter and the Lambda function is responsible for provisioning a user profile in the Sagemaker Studio domain based on the provided username.

## Python / Nodejs
The Python and nodejs code in this repository is used to implement the logic of the Lambda function that handles the single sign-on process. The code is located in the lambda_function.py file.


## Usage
Clone the repository and navigate to the directory

```bash
git clone https://github.com/[username]/sagemaker-studio-sso
cd sagemaker-studio-sso
```
Zip the lambda function (python)

```bash
cd src/python
zip -x __pycache__/ -r ../../lambda.zip ./
```

Initialize and apply the terraform
```
terraform init
terraform apply
```

Take the output of the terraform apply command and update the config.py file with the appropriate values.

Test the Lambda function by invoking it through the API Gateway.

Once the test is successful, You can use the API Gateway endpoint to integrate with your application for SSO

When you are done, you can destroy the resources created by running

```terraform
terraform destroy
```

## Troubleshooting
Make sure that your AWS CLI is configured correctly and that you have the appropriate permissions to create and manage resources in your AWS account.

The Lambda function assumes that you have already set up a domain in SageMaker Studio. If you haven't, you will need to do so before deploying this code.

If you have any issues with the terraform code, validate the syntax by running terraform validate and check the error message.

If you have any issues with the Lambda function, check the CloudWatch logs for more information.

## Note
This is a sample code for POC and it is not production ready and it is recommended to test the code with test account before using it in production.

Please let me know if there is any additional information you would like me to include in the README.