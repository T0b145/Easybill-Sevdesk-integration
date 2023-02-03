import os
import time
import logging
import argparse

from sevdesk import sevdesk
from easybill import easybill

def create_voucher(document, filename):
    if document["type"] == "INVOICE":
        creditDebit = "D"
    elif document["type"] == "CREDIT":
        creditDebit = "C"
    else:
        creditDebit = "Fehler"
        logging.error("creditDebit unclear")

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

if __name__ == "__main__":
    #### SETUP ####
    #setup API Access
    EASYBILL_API_KEY = os.getenv('EASYBILL_API_KEY')
    eb = easybill(EASYBILL_API_KEY)

    SEVDESK_API_KEY = os.getenv('SEVDESK_API_KEY')
    sd = sevdesk(SEVDESK_API_KEY)

    #setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(asctime)s %(message)s")

    #setup command line arguments to select invoices & test cycle
    parser = argparse.ArgumentParser('--invoice_list <inv-1,inv-2>'+'--dates <2023-01-01,2023-01-31> ')
    parser.add_argument('-l', '--invoice_list', help='Provide a list of invoices (comma seperated)')
    parser.add_argument('-d', '--document_date', help='Provide a document_date horizon (comma seperated)')
    parser.add_argument('-t', '--test', action='store_true')
    
    args = parser.parse_args()
    invoice_list = args.invoice_list
    document_date = args.document_date
    test_flag = args.test

    #define invoice filter
    filter={"type":"INVOICE,CREDIT", "is_archive":"0", "is_draft":"0", "limit":1000}
    if invoice_list:
        filter["number"]=str(invoice_list)
    elif document_date:
        filter["document_date"]=str(document_date)
    else:
        raise ValueError('Provide a invoice_list or document_date. See Command Line Arguments')

    #### RUN ####
    if test_flag:
        logging.info("This is a test, no invoices are transfered")

    #Get Relevant Invoices from Sevdesk
    #filter={"document_date": "2023-02-01,2030-12-31", "type":"INVOICE,CREDIT", "is_archive":"0", "is_draft":"0"}
    uploaded_list = []
    documents = eb.get_documents(filter)
    if documents["items"] == []:
        logging.info("No invoices in easybill found.")

    # Iterate over documents
    for document in documents["items"]:
        logging.debug("Document: {}".format(document["number"]))        
        #Validate if no replica
        if document["is_replica"] is True:
            logging.debug("Document is replica")
            continue

        #Validate if invoice is already available in Sevdesk
        voucher_check = sd.get_vouchers(filter={"descriptionLike": document["number"]})["objects"]
        if voucher_check != []:
            logging.debug("Document already available in SevDesk")
            continue

        #Stop if run is only for testing
        if test_flag:
            uploaded_list.append(document["number"])
            logging.info("Voucher would have been booked: {}".format(document["number"]))
            continue

        #Get pdf file from Easybill
        pdf_file = eb.get_document_pdf(document["id"])

        #Upload file to sevdesk and save filename
        filename = sd.upload_voucher_file(pdf_file, file_name="{}.pdf".format(document["number"]))

        #Create Voucher and upload to sevdesk
        voucher_data = create_voucher(document, filename)
        voucher = sd.post_voucher(voucher_data)
        tag = sd.add_tag(voucher_id=voucher["objects"]["voucher"]["id"], tag_name="easybill_api")
        logging.debug("Voucher successfully uploaded to SevDesk")

        # Book the voucher
        checkaccount_id=5339839 #Amazon Konto ID in Sevdesk
        amount = float(voucher['objects']['voucher']['sumGross'])
        date = voucher['objects']['voucher']['voucherDate']
        booked_voucher = sd.book_voucher(voucher_id=voucher["objects"]["voucher"]["id"], checkaccount_id=checkaccount_id, amount=amount, date=date)
        uploaded_list.append(document["number"])
        logging.info("Voucher booked: {}".format(document["number"]))

    logging.debug("Done!!!")