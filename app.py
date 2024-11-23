from flask import Flask, render_template, request, jsonify
import requests
import os
import time
from datetime import datetime
from pytz import timezone

app = Flask(__name__)

# Ganti dengan akses token asli Anda
USER_ACCESS_TOKEN = "YOUR_ACCES_TOKEN"


def get_page_list(user_access_token):
    """
    Mengambil daftar halaman berdasarkan user access token.
    """
    url = f"https://graph.facebook.com/v16.0/me/accounts?access_token={user_access_token}"
    response = requests.get(url)
    if response.status_code == 200:
        pages = response.json().get("data", [])
        return pages
    else:
        return []


def upload_media_to_facebook(page_id, page_access_token, media_path, description, publish_time=None):
    """
    Unggah media (gambar/video) ke halaman Facebook.
    """
    media_type = "video" if media_path.endswith((".mp4", ".mov")) else "photo"
    url = f"https://graph.facebook.com/v16.0/{page_id}/{media_type}s"

    files = {'source': open(media_path, 'rb')}
    data = {
        'access_token': page_access_token,
        'description': description,
    }

    if publish_time:
        data['scheduled_publish_time'] = publish_time
        data['published'] = False

    response = requests.post(url, files=files, data=data)
    return response.json()


@app.route('/')
def index():
    """
    Halaman utama dengan form upload media.
    """
    pages = get_page_list(USER_ACCESS_TOKEN)
    return render_template('index.html', pages=pages)


@app.route('/upload', methods=['POST'])
def upload_media():
    """
    Endpoint untuk mengunggah video dan gambar.
    """
    try:
        selected_pages = request.form.getlist('pages')  # List halaman yang dipilih
        descriptions = request.form.getlist('description[]')  # Deskripsi dari form
        schedule_times = request.form.getlist('schedule_time[]')  # Jadwal dari form
        media_files = request.files.getlist('media[]')  # List file media

        for i, media in enumerate(media_files):
            file_path = f"temp_{int(time.time())}_{i}.{media.filename.split('.')[-1]}"
            media.save(file_path)

            # Parsing waktu jadwal
            schedule_time = schedule_times[i]
            if schedule_time:
                local_time = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')
                jakarta_tz = timezone('Asia/Jakarta')
                local_time = jakarta_tz.localize(local_time)
                utc_time = local_time.astimezone(timezone('UTC'))
                publish_time = int(utc_time.timestamp())
            else:
                publish_time = None

            for page in selected_pages:
                page_id, page_access_token = page.split('|')
                response = upload_media_to_facebook(page_id, page_access_token, file_path, descriptions[i], publish_time)
                print(f"Response for {media.filename}: {response}")

            os.remove(file_path)

        return jsonify({"status": "success", "message": "Media berhasil diupload ke semua halaman!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
