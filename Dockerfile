# Use the official Python base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install the dependencies
COPY requirements.txt .
RUN pip install  -r requirements.txt

# Copy the Flask application code into the container
COPY . .

# Expose the port your Flask application will be listening on
EXPOSE 5000

# Set the environment variable for Flask
ENV FLASK_APP=doc_understanding.py

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

