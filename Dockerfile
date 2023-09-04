# Use the official Python 3.10 image as the base image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install the Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY *.py /app/

# Copy persistence files
COPY iss_bot_persisted /app/persistent_data/iss_bot_persisted

# Specify the command to run your application
CMD [ "python", "issBot.py" ]