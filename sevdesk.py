from datetime import datetime
import requests
import json

class sevdesk:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.API_URL = "https://my.sevdesk.de/api/v1/"
        self.headers = {"Authorization":self.API_KEY}

    def upload_voucher_file(self, file, file_name):
        url = self.API_URL + "Voucher/Factory/uploadTempFile"
        files={'file': (file_name, file, 'application/pdf')}
        r = requests.post(url, headers=self.headers, files=files)
        if r.status_code == 201:
            return r.json()["objects"]["filename"]
        else:
            print ("Dokument konnte nicht Hochgeladen werden")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def get_vouchers(self, filter={"status": 50}):
        url = self.API_URL + "Voucher"
        payload = filter
        r = requests.get(url, headers=self.headers, params=payload)
        if r.status_code == 200:
            return r.json()
        else:
            print ("Voucher konnte nicht abgerufen werden")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def get_voucher_pos(self, voucher_id):
        url = self.API_URL + "VoucherPos"
        payload = {"voucher[id]": voucher_id, "voucher[objectName]":"Voucher"}
        r = requests.get(url, headers=self.headers, params=payload)
        if r.status_code == 200:
            return r.json()
        else:
            print ("Voucher_Pos konnte nicht abgerufen werden")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def post_voucher(self, voucher_data):
        url = self.API_URL + "Voucher/Factory/saveVoucher"
        data = voucher_data
        r = requests.post(url, headers=self.headers, json=data)
        if r.status_code == 201:
            return r.json()
        else:
            print ("Fehler beim Voucher erstellen")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def update_voucher_pos_at(self, voucher_pos_id, accounting_type_id):
        url = self.API_URL + "VoucherPos/{}".format(voucher_pos_id)
        data = {"accountingType": {"id": accounting_type_id, "objectName": "AccountingType"}}
        r = requests.put(url, headers=self.headers, json=data)
        if r.status_code == 200:
            return r.json()
        else:
            print ("Voucher_Pos_AccountingType konnte nicht aktualisiert werden")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def update_voucher(self, voucher_id, data):
        url = self.API_URL + "Voucher/{}".format(voucher_id)
        data = data
        r = requests.put(url, headers=self.headers, json=data)
        if r.status_code == 200:
            return r.json()
        else:
            print("An error occurred while updating the voucher status")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def book_voucher(self, voucher_id, checkaccount_id, amount):
        url = self.API_URL + "Voucher/{}/bookAmount".format(voucher_id)
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {"checkAccount": {"id": checkaccount_id, "objectName":"CheckAccount"}, "amount": amount, "date": current_time, "type": "N"}
        r = requests.put(url, headers=self.headers, json=data)
        if r.status_code == 200:
            return r.json()
        else:
            print("An error occurred while booking the voucher")
            print("Status Code: ", r.status_code)
            print("Error message: ", r.json())

    def get_transactions(self):
        url = self.API_URL + "CheckAccountTransaction"
        #payload = {"status": status}
        r = requests.get(url, headers=self.headers)
        return r

if __name__ == "__main__":
    #Load Environment variables
    from dotenv import load_dotenv
    import os
    load_dotenv()

    SEVDESK_API_KEY = os.getenv('SEVDESK_API_KEY')
    sd = sevdesk(SEVDESK_API_KEY)

    #check ob voucher vorhanden
    #voucher = sd.get_vouchers(filter={"descriptionLike": 'RG-23-030695'})["objects"]
    #if voucher:
    #    print("vorhande")
    #else:
    #    print("nnicht vorhande")

    file = open("test.pdf",'rb')
    file_no = sd.upload_voucher_file(file)

    print (file_no)



    
