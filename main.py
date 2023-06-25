from flask import Flask, request, Response
import os
import urllib.parse
from logic.sms import send_sms
import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from urllib.parse import parse_qs

app = Flask(__name__)

mongodb = MongoClient("mongodb+srv://ernesteshun456:12345@cluster0.ngnrfiv.mongodb.net/ussd?retryWrites=true&w=majority")
db = mongodb["afrika"]
message_collection = db['msglog']
ussd_collection = db["uslog"]

response = ""


@app.before_request
def log_request_info():
    app.logger.debug("Headers: %s", request.headers)
    app.logger.debug("Body: %s", request.get_data())


@app.route("/sms/callback", methods=["POST", "GET"])
async def sms_send():
    data = request.get_json() 
    recipients = data.get("recipients") 
    message = data.get("message")
    status =  send_sms().sending(recipients, message)
    if status == 0: return Response(status=200)
    else: return Response(status=400)

@app.route('/sms/incoming', methods=['POST'])
def incoming_messages():
    data = request.get_data(as_text=True)
    parsed_data = parse_qs(data)

    phone_number = parsed_data.get('from', [''])[0]
    message = parsed_data.get('text', [''])[0]
    message_id = parsed_data.get('id', [''])[0]
    timestamp = parsed_data.get('date', [''])[0]

    message_collection.insert_one({"recipients": phone_number, "message": message, "id": message_id, "timestamp": timestamp})

    return Response(status=200)

@app.route('/sms/delivery-reports', methods=['POST'])
def delivery_reports():
    data = request.get_data(as_text=True)
    parsed_data = parse_qs(data)
    phone_number = parsed_data.get('phoneNumber', [''])[0]
    failure_reason = parsed_data.get('failureReason', [''])[0]
    report_id = parsed_data.get('id', [''])[0]
    status = parsed_data.get('status', [''])[0]
    network_code = parsed_data.get('networkCode', [''])[0]
    return Response(status=200)

@app.route("/", methods=["POST", "GET"])
async def ussd_callback():
    """Respond to ussd callback."""
    encoded_body = request.data
    decoded_body = urllib.parse.unquote(encoded_body.decode("utf-8"))
    pairs = decoded_body.split("&")
    dict = {}
    for i in pairs:
        key, value = i.split("=")
        dict[key] = urllib.parse.unquote(value)

    service_code = dict.get("serviceCode", None)
    phone_number = dict.get("phoneNumber", None)
    
    ussd_collection.insert_one({"recipients": phone_number, "serviceCode": service_code})


    text = dict.get("text", "")

    if text == "":
        response = "CON Welcome to Geek Bank \n"
        response += "1. Transfer \n"
        response += "2. Airtime & Data \n"
        response += "3. Account management \n"
    elif text == "1":
        response = "CON Choose your prefered mode \n"
        response += "1. Voice mode \n"
        response += "2. Text mode"
    elif text == "1*1":
        response = "END We are too broke to pay"
    elif text == "1*2":
        response = "CON Enter your Account ID "
    elif text.startswith("1*2*"):
        split_text = text.split("*")
        if len(split_text) == 3:
            account_id = split_text[2]
            response = "CON Enter the recipient's phone number "
        elif len(split_text) == 4:
            recipient_phone = split_text[3]
            response = "CON Enter the amount to send "
        elif len(split_text) == 5:
            amount = split_text[4]
            response = "END Transfer successful. Thank you!"
            end_mes = "You have successfully tranfered " + amount + " to " + phone_number
            status = send_sms().sending([phone_number], end_mes)

    elif text == "2":
        response = "CON Whitch network \n"
        response += "1- MTN"
        response += "2- Airtel"
        response += "3- Vodaphone"
        response += "4- International"
    elif text == "3":
        response = "END Your balance is on its way to you"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", default=3000), debug=True)
