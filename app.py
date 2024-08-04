from flask import Flask, request, redirect, session, url_for, render_template, jsonify
from dotenv import load_dotenv
import os
import base64
import requests
from requests import post, get
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print("No Artists with this name exists")
        return None
    return json_result[0]

def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result[:5]

def get_albums_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result[:3]

def get_related_artists_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["artists"]
    return json_result[:5]

def get_playlists_from_artist(token, artist_name):
    url = f"https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=playlist&limit=10"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["playlists"]["items"]
    if len(json_result) == 0:
        print("No playlists with selected artist")
        return None
    return json_result[:5]

def format_number_with_commas(number):
    return f"{number:,}"

app.jinja_env.filters['comma'] = format_number_with_commas

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/authorize')
def authorize():
    auth_url = ("https://accounts.spotify.com/authorize"
                "?response_type=code"
                f"&client_id={client_id}"
                f"&scope=user-top-read"
                f"&redirect_uri={redirect_uri}")
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    auth_token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    response = requests.post(auth_token_url, headers=headers, data=data)
    response_data = response.json()
    session['token'] = response_data['access_token']
    return redirect(url_for('search'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))

    if request.method == 'POST':
        artist_name = request.form['artist_name']
    else:
        artist_name = None

    if not artist_name:
        return render_template('search.html', error="Please enter an artist name to search.")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    result = search_for_artist(token, artist_name)
    if not result:
        return render_template('search.html', error="Artist not found")

    artist_id = result["id"]

    songs = get_songs_by_artist(token, artist_id)
    albums = get_albums_by_artist(token, artist_id)
    related_artists = get_related_artists_by_artist(token, artist_id)
    playlists = get_playlists_from_artist(token, artist_name)

    return render_template('search.html', artist=result, songs=songs, albums=albums, related_artists=related_artists, playlists=playlists)

@app.route('/get_album_info')
def get_album_info():
    token = session.get('token')
    id = request.args.get('playlist_id')
    type = request.args.get('type')

    headers = {
        "Authorization": f"Bearer {token}"
    }

    if type == 'playlist':
        url = f"https://api.spotify.com/v1/playlists/{id}"
    elif type == 'album':
        url = f"https://api.spotify.com/v1/albums/{id}"
    else:
        return jsonify({'error': 'Invalid type'}), 400

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to retrieve information'}), response.status_code

    info = response.json()

    try:
        info_data = {
            'name': info['name'],
            'release_date': info.get('release_date', 'N/A'),
            'total_tracks': info['tracks']['total'],
            'id': info['id']
        }
    except KeyError as e:
        return jsonify({'error': f"KeyError: {e}"}), 500

    return jsonify(info_data)

if __name__ == '__main__':
    app.run(port=8888)
