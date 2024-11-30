import re
import json

checklist = ['_', ' ']
def check_char_limit(data):
    if isinstance(data, str):
        cleaned_text = re.sub(r'[^A-Za-z0-9\s]', '', data)
        cleaned_text = cleaned_text.replace("\n", " ")
        data = cleaned_text.replace("\t", " ")
        if len(data) > 100:
            return data[0:99]
    return data


def condense(data):
    for i in checklist:
        data = data.replace(i, "")
    data = data.lower()
    if 'billnumber' in data:
        return 'bill_number'
    if 'billingaddress' in data:
        return 'billing_address'
    if 'customername' in data:
        return 'customer_name'
    if "date" in data:
        return "date" 
    # if "unitprice" in data or 'amount' in data:
    if "unitprice" in data:
        return "rate"
    if "due" in data:
        if "date" in data:
            return "due_date"
    return data


def parse_json(payload):
    parsed_payload = {}
    keys = list(payload.keys())
    parsed_payload['InvoiceNumber'] = payload['InvoiceNumber']
    #print(keys)
    for k in keys:
        # #print(k)
        if k != 'InvoiceNumber' and not isinstance(payload[k], list):
            # #print(payload[k]['value'])
            if k == 'InvoiceDate':
                parsed_payload['date'] =  payload[k]['value']
            key_name = condense(k.lower())
            parsed_payload[key_name] =  payload[k]['value']
        if isinstance(payload[k], list):
            total_items = []
            for i in range(len(payload[k])):
                items = {}
                item_keys = list(payload[k][i].keys())
                for j in item_keys:
                    # if j.lower() == 'unitprice':
                    key_name = condense(j.lower())
                        # items['rate'] = check_char_limit(payload[k][i][j]['value'])
                    items[key_name] =  check_char_limit(payload[k][i][j]['value'])
                total_items.append(items)
            parsed_payload["line_items"] =  total_items
        
    # parsed_payload = json.dumps(parsed_payload)
    return parsed_payload


def decode_bytes_in_dict(data):
    # Recursively decode any bytes objects found in dictionaries or lists
    if isinstance(data, dict):
        return {k: decode_bytes_in_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [decode_bytes_in_dict(item) for item in data]
    elif isinstance(data, bytes):
        return data.decode('utf-8')  # Decode bytes to string
    else:
        return data


def zoho_books(ORGANIZATION_ID, CUSTOMER_ID, access_token, conn, filepath, GST_NO, TAX_ID, logger):
    try:
        vendor_id = "vendor id pass from env"
        account_id = "Account ID pass from env"
        logger.info("In CRM")
        print("In CRM")
        #print(filepath)
        with open(filepath, 'r') as f:
            json_payload = json.load(f)
        for i in range(len(json_payload)):
            parser_payload = parse_json(json_payload[i])
            parser_payload["customer_id"] = CUSTOMER_ID 
            parser_payload['gst_no'] = GST_NO
            parser_payload['vendor_id'] = vendor_id
            for j in range(len(parser_payload['line_items'])):
                if 'name' not in parser_payload['line_items'][j]:
                    parser_payload['line_items'][j]['name'] = parser_payload['line_items'][j]['description']
                    parser_payload['line_items'][j]['description'] = ""
                parser_payload['line_items'][j]["tax_id"] = TAX_ID
                parser_payload['line_items'][j]["account_id"] = account_id

            decoded_data = decode_bytes_in_dict(parser_payload)
            payload = json.dumps(decoded_data).encode('utf-8')

            headers = {
                'Authorization': f"Zoho-oauthtoken {access_token}",
                'content-type': "application/json"
                }

            # conn.request("POST", f"/books/v3/invoices?organization_id={ORGANIZATION_ID}", payload, headers)
            conn.request("POST", f"/books/v3/bills?organization_id={ORGANIZATION_ID}", payload, headers)

            res = conn.getresponse()
            data = res.read()
            code_id = json.loads(data.decode())
            logger.info(code_id['message'])
            print(code_id['message'])

            # #print(data.decode("utf-8"))
        code_id = json.loads(data.decode())
        if code_id['code'] == 0 or code_id['code'] == '0':
            return {"status": "success", "message": "Invoice Created"}
        logger.info(code_id['message'])
        print(code_id['message'])
        return {"status": "success", "message": code_id['message']}
    except Exception as e:
        logger.info(e)
        print(e)
        return {"status": "failure", "message": e}