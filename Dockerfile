# Base Image
FROM python:3.11-slim AS base

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

#EXPOSE 5000
#EXPOSE 5679
# Install debugging tools
RUN apt update && apt install -y nano curl iputils-ping poppler-utils procps

# Debugging command for Quart
#CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "0.0.0.0:5679", "--wait-for-client", "-m", "hypercorn", "app:app", "--bind", "0.0.0.0:5000", "--reload"]
#CMD ["python", "-Xfrozen_modules=off", "app.py"]
CMD ["python", "-Xfrozen_modules=off", "app.py"]

###### PRODUCTION ########
FROM base AS prod

# Expose the port Quart runs on
EXPOSE 5000
CMD ["python", "-Xfrozen_modules=off", "app.py"]