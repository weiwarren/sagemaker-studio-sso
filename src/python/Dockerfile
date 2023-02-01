FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

COPY . .

# install lambda runtime interface
RUN pip3 install awslambdaric boto3

ENTRYPOINT [ "python3", "-m", "awslambdaric" ]

CMD [ "app.handler" ]