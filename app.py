import os
import shutil
import time
from sevdesk import sevdesk
from easybill import easybill

#Load .env file
from dotenv import load_dotenv
load_dotenv()

def create_voucher(document, filename):
    if document["type"] == "INVOICE":
        creditDebit = "D"
    elif document["type"] == "CREDIT":
        creditDebit = "C"
    else:
        creditDebit = "Fehler"
        print("creditDebit unklar")


    voucher_template = {
    "voucher": {
        "objectName": "Voucher",
        "mapAll": True,
        "voucherDate": document["document_date"],
        "supplierName": document['customer_snapshot']['display_name'],
        "description": document['number'],
        "payDate": document['paid_at'],
        "status": 100,
        "taxType": "default",
        "creditDebit": creditDebit,
        "voucherType": "VOU",
        "currency": document['currency'],
        "deliveryDate": document["document_date"]
    },
    "voucherPosSave": [{
        "objectName": "VoucherPos",
        "mapAll": True,
        "accountingType": {
        "id": 26,
        "objectName": "AccountingType"
        },
        "taxRate": document['items'][0]['vat_percent'],
        "net": "false",
        "isAsset": "false",
        "sumNet": document['amount_net']/100,
        "sumGross": document['amount']/100
    }],
    "filename": filename
    }
    return voucher_template

def upload_and_book_invoice(file_path):
    API_KEY = os.getenv('SEVDESK_API_KEY')
    sd = sevdesk(API_KEY)

    # Upload File
    upload = sd.upload_voucher(file_path)
    voucher_id = upload["objects"]["id"]
    print ("Document: ", file_path)
    #voucher_id = 55531635
    time.sleep(3) # to Analyze the file

    # Update Voucher Position for correct accounting Type
    voucher_pos = sd.get_voucher_pos(voucher_id=voucher_id)
    voucher_pos_id = voucher_pos["objects"][0]["id"]
    new_at = 26
    updated_vocher_pos = sd.update_voucher_pos_at(voucher_pos_id=voucher_pos_id, accounting_type_id=new_at)

    # Update Status and Supplier/Kunde
    data = {"status": 100, "supplierName":"Amazon Kunde"}
    updated_voucher = sd.update_voucher(voucher_id=voucher_id, data=data)

    # Book the voucher
    checkaccount_id=5339839
    amount = float(updated_voucher["objects"]["sumGross"])
    booked_voucher = sd.book_voucher(voucher_id=voucher_id, checkaccount_id=checkaccount_id, amount=amount)

if __name__ == "__main__":
    EASYBILL_API_KEY = os.getenv('EASYBILL_API_KEY')
    eb = easybill(EASYBILL_API_KEY)

    SEVDESK_API_KEY = os.getenv('SEVDESK_API_KEY')
    sd = sevdesk(SEVDESK_API_KEY)

    #Get Relevant Invoices from Sevdesk
    filter={"number": "202310026", "type":"INVOICE,CREDIT", "is_archive":"0", "is_draft":"0"}
    #filter={"document_date": "2023-02-01,2030-12-31", "type":"INVOICE,CREDIT", "is_archive":"0", "is_draft":"0"}
    documents = eb.get_documents(filter)

    # Iterate over documents
    for document in documents["items"]:        
        #Validate if no replica
        if document["is_replica"] is True:
            print ("Document is replica")
            continue

        #Validate if invoice is already available in Sevdesk
        voucher_check = sd.get_vouchers(filter={"descriptionLike": document["number"]})["objects"]
        if voucher_check != []:
            print ("Document already available in SevDesk")
            continue

        #Get pdf file from Sevdesk
        pdf_file = eb.get_document_pdf(document["id"])

        #Upload file to sevdesk and save filename
        filename = sd.upload_voucher_file(pdf_file, file_name="{}.pdf".format(document["number"]))

        #Create Voucher and upload to sevdesk
        voucher_data = create_voucher(document, filename)
        voucher = sd.post_voucher(voucher_data)
    
