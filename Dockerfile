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

#FROM base AS debug

#RUN pip install debugpy
#RUN apt update
#RUN apt install nano curl iputils-ping -y

#CMD python -m debugpy --listen 0.0.0.0:5679 --wait-for-client -m flask run -h 0.0.0.0 -p 5000

# Expose the port
#EXPOSE 4000

###### PRODUCTION ########
#FROM base AS prod
EXPOSE 0.0.0.0:5000

# Command to run the application
CMD ["python", "app.py"]

# Command to run the application
#CMD ["python", "app.py"]

#RUN apt-get update && apt-get install -y python3-dev
#    && cd /usr/local/bin \
#    && ln -s /usr/bin/python3 python \
#    && pip3 install --upgrade pip

#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
#ENV DEBIAN_FRONTEND=noninteractive
#CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5679", "app.py"]
