# Documentation: https://www.easybill.de/api/#/document/get_documents

from datetime import datetime
import requests
import json
import logging

class easybill:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.API_URL = "https://api.easybill.de/rest/v1/"
        self.headers = {"Authorization": "Bearer "+ self.API_KEY}

    def get_documents(self,filter={"document_date": "2023-02-01,2030-12-31"}):
        url = self.API_URL + "documents"
        payload = filter
        r = requests.get(url, headers=self.headers, params=payload)
        if r.status_code == 200:
            return r.json()
        else:
            logging.error("Documents konnten nicht abgerufen werden")
            logging.error("Status Code: ", r.status_code)
            logging.error("Error message: ", r.json())
    
    def get_document_pdf(self,document_no):
        url = self.API_URL + "documents/{}/pdf".format(document_no)
        file = requests.get(url, headers=self.headers)
        if file.status_code == 200:
            return file.content
        else:
            logging.error("File konnte nicht runtergeladen werden")
            logging.error("Status Code: ", file.status_code)
            logging.error("Error message: ", file.json())


if __name__ == "__main__":
    # setup logging
    logging.basicConfig(level=logging.DEBUG)

    #Load Environment variables
    import os
    from dotenv import load_dotenv
    load_dotenv()

    EASYBILL_API_KEY = os.getenv('EASYBILL_API_KEY')

    eb = easybill(EASYBILL_API_KEY)
    filter={"number": "202310026", "type":"INVOICE,CREDIT", "is_archive":"0", "is_draft":"0"}
    #filter={"document_date": "2023-01-27,2030-12-31"}
    documents = eb.get_documents(filter)
    print (documents)
    
    #pdf = eb.get_document_pdf("2247836460")
    #with open("my_file.pdf", 'wb') as f:
    #    f.write(pdf)

