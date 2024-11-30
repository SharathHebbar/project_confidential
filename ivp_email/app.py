import os
import shutil
import logging
import queue
import uuid
import hashlib
import asyncio
from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from utils.send_email import get_attachments
from utils.parser import parse_documents

load_dotenv()

logging.basicConfig(
    filename='log_data.log',
    format='%(asctime)s %(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")

ENDPOINT = os.getenv("AZURE_INV_ENDPOINT")
KEY = os.getenv("AZURE_INV_PARSER_API_KEY")

ASSETS_DIR = os.getenv("ASSETS_DIR")
# ATTACHMENT_DIR = os.getenv("ATTACHMENT_DIR")
# FLAT_FILE_DIR = os.getenv("FLAT_FILE_DIR")

# Zoho Books
URL = os.getenv("URL")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
URI = os.getenv("URI")
ORGANIZATION_ID = int(os.getenv("ORGANIZATION_ID"))
CUSTOMER_ID = int(os.getenv("CUSTOMER_ID"))
GST_NO = os.getenv('GST_NO')
TAX_ID = os.getenv('TAX_ID')

# Initialize FastAPI app
app = FastAPI()

# Initialize queues
attachment_queue = queue.Queue()

def create_directory_if_not_exists(dir):
    if not os.path.isdir(dir):
        os.mkdir(dir)
    else:
        shutil.rmtree(dir)
        os.mkdir(dir)

user_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:10]

async def process_invoice():
    try:
        logger.info("Process Started")
        create_directory_if_not_exists(ASSETS_DIR)
        USER_ASSETS_DIR = os.path.join(ASSETS_DIR, user_id)
        create_directory_if_not_exists(USER_ASSETS_DIR)

        ATTACHMENT_DIR = os.path.join(USER_ASSETS_DIR, "attachments")
        create_directory_if_not_exists(ATTACHMENT_DIR)
        
        FLAT_FILE_DIR = os.path.join(USER_ASSETS_DIR, "flat_files")
        create_directory_if_not_exists(FLAT_FILE_DIR)

        logger.info("Create Directories Successfully")
        email_status = get_attachments(EMAIL, PASSWORD, IMAP_SERVER, ATTACHMENT_DIR, attachment_queue, logger)

        if email_status['status'].lower() == 'failure':
            raise HTTPException(status_code=500, detail=str(email_status['message']))
        logger.info("Complete Email Process")
        logger.info(email_status['message'])

        if not attachment_queue.empty():
            parsed_data = parse_documents(
                ENDPOINT
                , KEY
                , FLAT_FILE_DIR
                , attachment_queue
                , URL
                , REFRESH_TOKEN
                , CLIENT_ID
                , CLIENT_SECRET
                , URI
                , ORGANIZATION_ID
                , CUSTOMER_ID
                , GST_NO
                , TAX_ID
                , logger
            )

            if parsed_data['status'].lower() == 'failure':
                raise HTTPException(status_code=500, detail=str(parsed_data['message']))
            logger.info("Complete Parsing Process")
            logger.info(parsed_data['message'])

        # Wait for a minute before the next check
        await asyncio.sleep(60)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Wrapper function to run the async function in the scheduler
def run_process_invoice():
    asyncio.run(process_invoice())

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_process_invoice, 'interval', minutes=3)  # Check every minute
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "Email Processor is running."}