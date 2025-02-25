# Base Image
FROM python:3.9-slim AS base

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

####### DEBUG ###########
FROM base AS debug

# Install debugging tools
RUN pip install debugpy
RUN apt update && apt install -y nano curl iputils-ping poppler-utils

# Debugging command
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5679", "--wait-for-client", "-m", "flask", "run", "-h", "0.0.0.0", "-p", "5000"]

###### PRODUCTION ########
FROM base AS prod

# Install Gunicorn for production
RUN pip install gunicorn

# Expose the port Flask runs on
EXPOSE 5000

# Run the app with Gunicorn in production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]