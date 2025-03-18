import csv
import os
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Twilio credentials (set these as environment variables for security)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
AUDIO_FILE_URL = "https://your-hosted-audio-file.mp3"  # Replace with actual URL
CSV_FILE = "contacts.csv"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

def update_csv(phone_number, interested):
    rows = []
    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["Phone"] == phone_number:
                row["Interested"] = "YES" if interested else "NO"
            rows.append(row)
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def make_call(phone_number):
    call = twilio_client.calls.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        url="https://your-server.com/voice_response"
    )
    print(f"Calling {phone_number}, Call SID: {call.sid}")

@app.route("/voice_response", methods=["POST"])
def voice_response():
    response = VoiceResponse()
    response.play(AUDIO_FILE_URL)
    response.gather(numDigits=1, action="/handle_response", timeout=10)
    return Response(str(response), mimetype="text/xml")

@app.route("/handle_response", methods=["POST"])
def handle_response():
    digits = request.form.get("Digits")
    phone_number = request.form.get("From")
    
    if digits == "1":
        update_csv(phone_number, True)
    else:
        update_csv(phone_number, False)
    
    return Response("<Response><Hangup/></Response>", mimetype="text/xml")

def start_calls():
    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if "Interested" not in row or not row["Interested"]:
                make_call(row["Phone"])

if __name__ == "__main__":
    start_calls()
    app.run(host="0.0.0.0", port=5000)
