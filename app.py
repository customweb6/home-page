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
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "dgfki2il5"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY", "532393676845492"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET", "2sDHubfoJ5idJd7gDJ71SA0Gv50")
)

db = None
bucket = None

try:
    firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")
    if firebase_creds:
        service_account_info = json.loads(firebase_creds)
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {
            "storageBucket": "customweb-e6165.appspot.com"
        })
        db = firestore.client()
        bucket = storage.bucket()
        print("Firebase initialized successfully")
    else:
        print("Warning: FIREBASE_CREDENTIALS not found. Submission functionality will be disabled.")
except Exception as e:
    print(f"Warning: Failed to initialize Firebase: {e}. Submission functionality will be disabled.")


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
    if db is None:
        return render_template_string("""
            <html>
            <head><title>Service Unavailable</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>Submission Service Currently Unavailable</h2>
                <p>Firebase credentials are not configured. Please contact the administrator.</p>
                <a href="/" style="color: #007bff;">Return to Homepage</a>
            </body>
            </html>
        """)
    
    # Fetch form data
    business_name = request.form.get('businessName')
    email = request.form.get('email')
    business_description = request.form.get('businessDescription')
    business_location = request.form.get('businessLocation')
    featured_text = request.form.get('featuredText')
    notes = request.form.get('notes')
    management_plan = request.form.get("managementPlan")

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
        "email": email,
        "description": business_description,
        "location": business_location,
        "featuredText": featured_text,
        "notes": notes,
        "managementPlan": management_plan,
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
    port = int(os.environ.get("PORT", 5000))  # default to 5000 locally
    app.run(host="0.0.0.0", port=port, debug=False)
