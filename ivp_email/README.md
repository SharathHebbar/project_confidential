# Invoice Parser using Azure Invoice Parser and Python

# Flow Chart

1. The User sends a message to the register email.
2. The server gets triggered and reads that mail downloads attachment (invoice).
3. The invoices will be fed into queue for processing.
4. The invoices will be fed into invoice parser one by one
5. The parsed data will be converted into json and fed into the queue.
6. The jsons will be fed into Zoho books one by one from Queue

# How to use this system

## The directory structure is as follows
utils/
├── crm.py
├── parser.py
├── send_email.py

app.py
.env
Dockerfile
README.md
requirements.txt

## How to run this

1. First install the requirements `pip install -r requirements.txt`
2. Run `uvicorn app:app` to run the server

## Dockerize this Code

1. `docker login <server_name> -u <user_name> -p <password>` - Optional
2. Build a docker image `docker build -t <image_name> .`
3. Run the docker image `docker run --name <container_name> -p 80:80 <image_name>`


