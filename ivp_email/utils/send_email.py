import imaplib
import email
from email.header import decode_header
import os


def parse_email_id(email_id):
    email_id = str(email_id)
    email_sp_chars = ['@', '.']
    if '<' in email_id and '>' in email_id:
        st_idx = email_id.find('<') + 1
        end_idx = email_id.find('>')
        email_id = email_id[st_idx: end_idx]  # Extract the email address
    for j in email_sp_chars:
        email_id = email_id.replace(j, "_")  # Replace special characters
    return email_id

def get_attachments(EMAIL, PASSWORD, IMAP_SERVER, ATTACHMENT_DIR, attachment_queue, logger):
    try:
        logger.info("In Email Module")
        print("In Email Module")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_disposition() == "attachment":
                                filename = part.get_filename()
                                email_from = msg.get("From")  # Extract the 'From' header
                                # print(f"Email from: {email_from}")

                                if filename and email_from:
                                    # Parse the email ID and append it to the filename
                                    email_id_name = parse_email_id(email_from)
                                    # print(f"Parsed Email ID: {email_id_name}")

                                    # Create a new filename by appending the parsed email ID
                                    filename = email_id_name + "_" + filename

                                    # Save the attachment with the new filename
                                    filepath = os.path.join(ATTACHMENT_DIR, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))

                                    # Add the filepath to the attachment queue
                                    attachment_queue.put(filepath)

            mail.store(email_id, '+FLAGS', '\\Seen')
        mail.logout()
        return {"status": "success", "message": "Attachments downloaded and queued."}

    except Exception as e:
        logger.info(e)
        print(e)
        return {"status": "failure", "message": str(e)}