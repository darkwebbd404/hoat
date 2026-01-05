from flask import Flask, render_template, request
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import ReqCLan_pb2
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Encryption Keys
xK = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
xV = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    status = None
    detailed_msg = None

    if request.method == 'POST':
        try:
            # ফর্ম থেকে ডাটা নেওয়া
            uid = request.form.get('uid')
            password = request.form.get('password')
            clan_id = request.form.get('clan_id')
            region = request.form.get('region')

            if not uid or not password or not clan_id:
                raise Exception("Please fill in all fields correctly.")

            # 1. Server Selection
            req_url = ""
            if region == 'india':
                req_url = "https://client.ind.freefiremobile.com/RequestJoinClan"
            else:
                req_url = "https://clientbp.ggpolarbear.com/RequestJoinClan"

            # 2. Get JWT Token
            jwt_url = f"https://ctx-jwt-api.vercel.app/token?uid={uid}&password={password}"
            jwt_response = requests.get(jwt_url)
            
            if jwt_response.status_code != 200:
                raise Exception("Login Failed! Please check your UID & Password.")

            jwt_data = jwt_response.json()
            if 'token' not in jwt_data:
                raise Exception("System Error: Token not found.")
            
            jwt_token = jwt_data['token']

            # 3. Protobuf & Encryption
            msg = ReqCLan_pb2.MyMessage()
            msg.field_1 = int(clan_id)
            data_bytes = msg.SerializeToString()

            cipher = AES.new(xK, AES.MODE_CBC, xV)
            encrypted_data = cipher.encrypt(pad(data_bytes, AES.block_size))

            # 4. Request Headers
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 10; m3 note Build/QD4A.200805.003)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/octet-stream",
                'Authorization': f"Bearer {jwt_token}",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB51",
            }

            # 5. Send Request
            response = requests.post(req_url, headers=headers, data=encrypted_data)

            # --- Result Logic ---
            if response.status_code == 200:
                message = "✅ Clan Join Request Sent Successfully!"
                status = "success"
            elif region == 'india' and response.status_code == 400:
                # India Server Fix
                message = "⚠️ Request Sent (Status 400)"
                detailed_msg = "This is normal for India Server. Check in-game requests."
                status = "warning"
            else:
                message = f"❌ Request Failed! (Code: {response.status_code})"
                detailed_msg = "Possible reasons: Clan full, Level requirement not met, or Server issue."
                status = "danger"

        except Exception as e:
            message = "⚠️ Error Occurred"
            detailed_msg = str(e)
            status = "danger"

    return render_template('index.html', message=message, status=status, detailed_msg=detailed_msg)

if __name__ == '__main__':
    app.run(debug=True)
