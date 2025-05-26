# Use Python 3.11.8 as base image
FROM python:3.11.8

# Set working directory inside the container
WORKDIR /code

# Copy requirements and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Install python-dotenv for loading the .env file
RUN pip install python-dotenv

# Install AWS CLI
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

# Copy the .env file into the container
COPY ./.env /code/.env

# Copy the Python script that configures AWS CLI
COPY ./set_key.py /code/set_key.py

# Copy the rest of the application code
COPY ./app /code/app

# Expose port 8000
EXPOSE 8000

# First, run set_key.py to configure AWS CLI, then start the FastAPI app
CMD ["sh", "-c", "python /code/set_key.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]