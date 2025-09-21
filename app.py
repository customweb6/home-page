from flask import Flask, request, render_template_string,render_template
import os
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore, storage
import cloudinary
import cloudinary.uploader
import cloudinary.api
import json

# configure Cloudinary with your credentials
cloudinary.config( 
  cloud_name = "dgfki2il5", 
  api_key = "532393676845492", 
  api_secret = "2sDHubfoJ5idJd7gDJ71SA0Gv50" 
)

firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")
cred_dict = json.loads(firebase_creds)
cred = credentials.Certificate(cred_dict)

# Initialize Firebase with storage bucket
firebase_admin.initialize_app(cred, {
    "storageBucket": "customweb-e6165.appspot.com"
})

# Initialize Firestore and Storage clients
db = firestore.client()
bucket = storage.bucket()


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Homepage
@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/entry')
def form():
    return render_template("entry.html")

@app.route('/submit-business', methods=['POST'])
def submit_business():
    # Fetch form data
    business_name = request.form.get('businessName')
    business_description = request.form.get('businessDescription')
    business_location = request.form.get('businessLocation')
    featured_text = request.form.get('featuredText')
    notes = request.form.get('notes')

    media_files = request.files.getlist('mediaUpload')
    uploaded_urls = []

    for file in media_files:
        if file and file.filename:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file, folder=f"businesses/{business_name}")
            uploaded_urls.append(result['secure_url'])

    # Save metadata + file URLs to Firestore
    business_data = {
        "name": business_name,
        "description": business_description,
        "location": business_location,
        "featuredText": featured_text,
        "notes": notes,
        "media": uploaded_urls
    }
    db.collection("businesses").add(business_data)

    # Render a proper template instead of plain HTML
    return render_template(
        "submission_received.html",
        business_name=business_name,
        file_count=len(uploaded_urls)
    )



if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # default to 5000 if not set
    app.run(host="0.0.0.0", port=port)
