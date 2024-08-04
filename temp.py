from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
genius_access_token = os.getenv("GENIUS_ACCESS_TOKEN")

# Retrieve api token
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url= "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

# Token authorization
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# Function to search for artist
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

# Function to get songs from artist
def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

# Function to get albums from artist
def get_albums_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result

# Function to get related artists
def get_related_artists_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["artists"]
    return json_result

# Function to access playlists with associated artist
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
    return json_result

# Function to get song lyrics from Genius
def get_song_lyrics(genius_access_token, song_name, artist_name):
    url = "https://api.genius.com/search"
    headers = {
        "Authorization": "Bearer " + genius_access_token
    }
    query = {"q": f"{song_name} {artist_name}"}
    response = get(url, headers=headers, params=query)
    json_result = response.json()

    if json_result["response"]["hits"]:
        song_path = json_result["response"]["hits"][0]["result"]["path"]
        return f"https://genius.com{song_path}"
    else:
        return "Lyrics not found"

# Initialize Functions
token = get_token()
artist_name = input("Enter the artist's name: ")
result = search_for_artist(token, artist_name)

if result:
    artist_id = result["id"]
    songs = get_songs_by_artist(token, artist_id)
    albums = get_albums_by_artist(token, artist_id)
    artists = get_related_artists_by_artist(token, artist_id)
    playlists = get_playlists_from_artist(token, artist_name)

    index1 = 0
    index2 = 0
    index3 = 0
    index4 = 0

    # Print top songs and their lyrics
    print("\n\nTop Songs")
    for index1, song in enumerate(songs):
        print(f"{index1 + 1}. {song['name']} (Popularity: {song['popularity']})")
        lyrics_url = get_song_lyrics(genius_access_token, song['name'], artist_name)
        print(f"Lyrics: {lyrics_url}")

    # Print top three unique albums
    print("\n\nTop Albums")
    printed_albums = set()
    count = 0
    for index2, album in enumerate(albums):
        if album['name'] not in printed_albums:
            print(f"{count + 1}. {album['name']}")
            printed_albums.add(album['name'])
            count += 1
            if count == 3:
                break

    # Print 5 related artists to selected artist
    print("\n\nRelated Artists")
    printed_artists = set()
    count = 0
    for index3, artist in enumerate(artists):
        if artist['name'] not in printed_artists:
            print(f"{count + 1}. {artist['name']}")
            printed_artists.add(artist['name'])
            count += 1
            if count == 5:
                break

    # Print playlists associated with the artist
    print("\n\nPlaylists")
    printed_playlists = set()
    if playlists:
        for index4, playlist in enumerate(playlists):
            if playlist['name'] not in printed_playlists:
                print(f"{index4 + 1}. {playlist['name']} (Owner: {playlist['owner']['display_name']})")
                print(f"URL: {playlist['external_urls']['spotify']}")
                printed_playlists.add(playlist['name'])
else:
    print("Artist not found.")
