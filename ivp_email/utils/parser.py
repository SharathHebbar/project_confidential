import os
from pathlib import Path
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import http.client
import requests
import uuid
import hashlib

from utils.crm import zoho_books


def get_bill_numbers(access_token, org_id):
    conn = http.client.HTTPSConnection("www.zohoapis.com")
    headers = { "Authorization": f"Zoho-oauthtoken {access_token}" }
    conn.request("GET", f"/books/v3/bills?organization_id={org_id}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    code_id = json.loads(data.decode("utf-8"))
    bill_numbers = [str(code_id['bills'][i]['bill_number']) for i in range(len(code_id['bills']))]
    return bill_numbers

    
def validate_bill_numbers(bill_number, bill_numbers:list):
    if bill_number not in bill_numbers:
        return bill_number
    new_bill_number = hashlib.sha256(str(uuid.uuid1()).encode()).hexdigest()[:10]
    return validate_bill_numbers(new_bill_number, bill_numbers)


def address_value(vendor_address):
    if vendor_address:
        house_number = vendor_address.value.house_number
        po_box = vendor_address.value.po_box
        road = vendor_address.value.road
        city = vendor_address.value.city
        state = vendor_address.value.state
        postal_code = vendor_address.value.postal_code
        country_region = vendor_address.value.country_region
        street_address = vendor_address.value.street_address
        unit = vendor_address.value.unit
        city_district = vendor_address.value.city_district
        state_district = vendor_address.value.state_district
        suburb = vendor_address.value.suburb
        house = vendor_address.value.house
        level = vendor_address.value.level

        vendor_address_value = ""

        if street_address:
            vendor_address_value += street_address + " "
        else:
            if house_number:
                vendor_address_value += house_number + " "
            if road:
                vendor_address_value += road + " "
        if house:
            vendor_address_value += house + " "
        if po_box:
            vendor_address_value += po_box + " "
        if city_district:
            vendor_address_value += city_district + " "
        if state_district:
            vendor_address_value += state_district + " "
        if state:
            vendor_address_value += state + " "
        if postal_code:
            vendor_address_value += postal_code
    return vendor_address_value
    

def parse_documents(ENDPOINT,
                    KEY,
                    FLAT_FILE_DIR,
                    attachment_queue,
                    URL,
                    REFRESH_TOKEN,
                    CLIENT_ID,
                    CLIENT_SECRET,
                    URI,
                    ORGANIZATION_ID,
                    CUSTOMER_ID,
                    GST_NO,
                    TAX_ID,
                    logger
                    ):
    try:
        logger.info("In Parser")
        print("In Parser")
        header_payload = {
                'refresh_token': REFRESH_TOKEN,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': URI,
                'grant_type': 'refresh_token'
        }
        response = requests.post(url=URL, data=header_payload)
        if response.status_code == 200:
            access_token = response.json()['access_token']
        conn = http.client.HTTPSConnection("www.zohoapis.com")
        while not attachment_queue.empty():

            filepath = attachment_queue.get()
            #print(filepath)
            document_analysis_client = DocumentAnalysisClient(
                endpoint=ENDPOINT,
                credential=AzureKeyCredential(KEY)
            )
            with open(filepath, "rb") as invoice_file:
                poller = document_analysis_client.begin_analyze_document(
                    "prebuilt-invoice",
                    document=invoice_file
                )
            invoices = poller.result()
            invoices_data = []

            for idx, invoice in enumerate(invoices.documents):
                invoice_data = {}  # Dictionary to hold this invoice's data
                invoice_data["InvoiceNumber"] = {
                    "value": idx + 1,
                    "confidence": 1
                }
                bill_no_list = get_bill_numbers(access_token, ORGANIZATION_ID)
                bill_number = validate_bill_numbers(str(idx + 1), bill_no_list)
                invoice_data["bill_number"] = {
                    "value": bill_number,
                    "confidence": 1
                }
                # Extract vendor details
                vendor_name = invoice.fields.get("VendorName")
                if vendor_name:
                    invoice_data["VendorName"] = {
                        "value": vendor_name.value,
                        "confidence": vendor_name.confidence
                    }
                
                vendor_address = invoice.fields.get("VendorAddress")
                if vendor_address:
                    house_number = vendor_address.value.house_number
                    po_box = vendor_address.value.po_box
                    road = vendor_address.value.road
                    city = vendor_address.value.city
                    state = vendor_address.value.state
                    postal_code = vendor_address.value.postal_code
                    country_region = vendor_address.value.country_region
                    street_address = vendor_address.value.street_address
                    unit = vendor_address.value.unit
                    city_district = vendor_address.value.city_district
                    state_district = vendor_address.value.state_district
                    suburb = vendor_address.value.suburb
                    house = vendor_address.value.house
                    level = vendor_address.value.level

                    vendor_address_value = ""

                    if street_address:
                        vendor_address_value += street_address + " "
                    else:
                        if house_number:
                            vendor_address_value += house_number + " "
                        if road:
                            vendor_address_value += road + " "
                    if house:
                        vendor_address_value += house + " "
                    if po_box:
                        vendor_address_value += po_box + " "
                    if city_district:
                        vendor_address_value += city_district + " "
                    if state_district:
                        vendor_address_value += state_district + " "
                    if state:
                        vendor_address_value += state + " "
                    if postal_code:
                        vendor_address_value += postal_code

                    invoice_data["VendorAddress"] = {
                        "value": vendor_address_value,
                        "confidence": vendor_address.confidence
                    }
                            
                # Extract customer details
                vendor_address_recipient = invoice.fields.get("VendorAddressRecipient")
                if vendor_address_recipient:
                    invoice_data["VendorAddressRecipient"] = {
                        "value": vendor_address_recipient.value,
                        "confidence": vendor_address_recipient.confidence
                    }

                customer_name = invoice.fields.get("CustomerName")
                if customer_name:
                    invoice_data["CustomerName"] = {
                        "value": customer_name.value,
                        "confidence": customer_name.confidence
                    }
                
                customer_id = invoice.fields.get("CustomerId")
                if customer_id:
                    invoice_data["CustomerId"] = {
                        "value": customer_id.value,
                        "confidence": customer_id.confidence
                    }
                customer_address = invoice.fields.get("CustomerAddress")
                if customer_address:
                    customer_add_value = address_value(customer_address)
                    invoice_data["CustomerAddress"] = {
                        "value": customer_add_value,
                        "confidence": customer_address.confidence
                    }
                customer_address_recipient = invoice.fields.get("CustomerAddressRecipient")
                if customer_address_recipient:
                    invoice_data["CustomerAddressRecipient"] = {
                        "value": customer_address_recipient.value,
                        "confidence": customer_address_recipient.confidence
                    }
                
                invoice_id = invoice.fields.get("InvoiceId")
                if invoice_id:
                    invoice_data["InvoiceId"] = {
                        "value": invoice_id.value,
                        "confidence": invoice_id.confidence
                    }

                invoice_date = invoice.fields.get("InvoiceDate")
                if invoice_date:
                    invoice_data["InvoiceDate"] = {
                        "value": str(invoice_date.value),
                        "confidence": invoice_date.confidence
                    }
                
                invoice_total = invoice.fields.get("InvoiceTotal")
                if invoice_total:
                    invoice_data["InvoiceTotal"] = {
                        "value": invoice_total.value.amount,
                        "confidence": invoice_total.confidence
                    }
                due_date = invoice.fields.get("DueDate")
                if due_date:
                    invoice_data["DueDate"] = {
                        "value": str(due_date.value),
                        "confidence": due_date.confidence
                    }
                billing_address = invoice.fields.get("BillingAddress")
                if billing_address:
                    billing_add_value = address_value(billing_address)
                    invoice_data["BillingAddress"] = {
                        "value": billing_add_value,
                        "confidence": billing_address.confidence
                    }
                billing_address_recipient = invoice.fields.get("BillingAddressRecipient")
                if billing_address_recipient:
                    invoice_data["BillingAddressRecipient"] = {
                        "value": billing_address_recipient.value,
                        "confidence": billing_address_recipient.confidence
                    }
                shipping_address = invoice.fields.get("ShippingAddress")
                if shipping_address:
                    invoice_data["ShippingAddress"] = {
                        "value": address_value(shipping_address),
                        "confidence": shipping_address.confidence
                    }
                shipping_address_recipient = invoice.fields.get("ShippingAddressRecipient")
                if shipping_address_recipient:
                    invoice_data["ShippingAddressRecipient"] = {
                        "value": shipping_address_recipient.value,
                        "confidence": shipping_address_recipient.confidence,
                    }
                amount_due = invoice.fields.get("AmountDue")
                if amount_due:
                    invoice_data["AmountDue"] = {
                        "value": amount_due.value.amount,
                        "confidence": amount_due.confidence,
                    }
            
                for idx, item in enumerate(invoice.fields.get("TaxDetails").value):
                    gst = item.value.get("Amount")
                    key_value = "gst"+str(idx)
                    if gst:
                        invoice_data[key_value] = {
                        "value": gst.value.amount,
                        "confidence": gst.confidence,
                        }

                # Extract invoice items
                items = []
                for item_idx, item in enumerate(invoice.fields.get("Items").value):
                    item_data = {}
                    item_description = item.value.get("Description")
                    if item_description:
                        item_data["Description"] = {
                            "value": item_description.value,
                            "confidence": item_description.confidence
                        }
                    
                    item_quantity = item.value.get("Quantity")
                    if item_quantity:
                        item_data["Quantity"] = {
                            "value": item_quantity.value,
                            "confidence": item_quantity.confidence
                        }
                    
                    item_unit_price = item.value.get("UnitPrice")
                    if item_unit_price:
                        item_data["UnitPrice"] = {
                            "value": item_unit_price.value.amount,
                            "confidence": item_unit_price.confidence
                        }
                    
                    item_amount = item.value.get("Amount")
                    if item_amount:
                        item_data["Amount"] = {
                            "value": item_amount.value.amount,
                            "confidence": item_amount.confidence
                        }

                    items.append(item_data)

                invoice_data["Items"] = items

                # Add the invoice data to the list
                invoices_data.append(invoice_data)
          
            parsed_file = Path(filepath).name
            parsed_data = parsed_file.split(".")[0] + ".json"
            parsed_data = os.path.join(FLAT_FILE_DIR, parsed_data)

            with open(parsed_data, "w") as f:
                json.dump(invoices_data, f)

            # json_queue.put(parsed_data)
            if parsed_data:
                crm_data = zoho_books(ORGANIZATION_ID, CUSTOMER_ID, access_token, conn, parsed_data, GST_NO, TAX_ID, logger)
                print(crm_data)
                if crm_data['status'] == 'failure':
                    logger.info(crm_data)
                
                    return {"status": "failure", "message": str(crm_data['message'])}

            attachment_queue.task_done()
        conn.close()
        return {"status": "success", "message": "All queued attachments have been processed."}
    except Exception as e:
        logger.info(e)
        print(e)
        return {"status": "failure", "message": e}