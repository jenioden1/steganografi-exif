from flask import Flask, render_template, request, redirect, url_for
import requests
from PIL import Image
import piexif
from io import BytesIO
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
CLIPDROP_API_KEY = 'aab046e16f6c4bd7f51b09ed682339467c43b647777a24e598c4c406302eb5eb42d526970095f7634dc908df448cd696'  # ← Ganti dengan API key kamu

secret_message = ""

@app.route('/', methods=['GET', 'POST'])
def index():
    global secret_message
    if request.method == 'POST':
        secret_message = request.form['message']
        return redirect(url_for('generate'))
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    global secret_message
    image_path = None
    embedded_image_path = None

    if request.method == 'POST':
        if 'generate' in request.form:
            prompt = "make me image abstract"
            response = requests.post(
                'https://clipdrop-api.co/text-to-image/v1',
                files={'prompt': (None, prompt)},
                headers={'x-api-key': CLIPDROP_API_KEY}
            )
            if response.ok:
                image = Image.open(BytesIO(response.content))
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'generated.png')
                image.save(image_path)
            else:
                return f"Error generating image: {response.status_code}"

        elif 'embed' in request.form:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'generated.png')
            image = Image.open(image_path)

            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = secret_message.encode('utf-8')
            exif_bytes = piexif.dump(exif_dict)

            embedded_path = os.path.join(app.config['UPLOAD_FOLDER'], 'embedded.png')
            image.save(embedded_path, exif=exif_bytes)
            embedded_image_path = embedded_path

    return render_template('generate.html', image_path=image_path, embedded_path=embedded_image_path)

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    extracted_message = None

    if request.method == "POST":
        if 'image' not in request.files:
            extracted_message = "⚠️ Tidak ada file yang diupload."
        else:
            file = request.files['image']
            if file.filename == '':
                extracted_message = "⚠️ Nama file kosong."
            else:
                try:
                    image = Image.open(file.stream)
                    exif_bytes = image.info.get("exif")

                    if not exif_bytes:
                        extracted_message = "❌ Tidak ada pesan yang disisipkan."
                    else:
                        exif_data = piexif.load(exif_bytes)
                        desc = exif_data["0th"].get(piexif.ImageIFD.ImageDescription)
                        if desc:
                            extracted_message = desc.decode("utf-8", errors="ignore")
                        else:
                            extracted_message = "❌ Tidak ada pesan yang disisipkan."
                except Exception as e:
                    extracted_message = f"⚠️ Terjadi kesalahan saat ekstraksi: {str(e)}"

    return render_template("extract.html", extracted_message=extracted_message)

if __name__ == '__main__':
    app.run(debug=True)
