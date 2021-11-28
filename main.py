import datetime
import json
import os
import random
import smtplib
import ssl
import time
import webbrowser
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


def authenticate(client_id, client_secret):
    auth_response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    return auth_response.json()['access_token']


def random_tracks(playlist_id):
    token = authenticate(os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET'))
    headers = {'Authorization': 'Bearer ' + token}

    playlist = requests.get('https://api.spotify.com/v1/playlists/' + playlist_id, headers=headers).json()

    previewable_items = list(filter(lambda i: i['track']['preview_url'] is not None, playlist['tracks']['items']))

    return list(map(lambda i: i['track'], random.choices(previewable_items, k=10)))


def choose_track(tracks):
    for idx, track in enumerate(tracks, 1):
        print('[{idx}]  {artist} - {title}'.format(idx=idx, artist=track['artists'][0]['name'], title=track['name']))

    choice = int(input("Enter song number: "))

    track = tracks[choice - 1]

    print('You have chosen {artist} - {title}'.format(artist=track['artists'][0]['name'], title=track['name']))

    return track


def load_people(seed):
    people = json.load(open('resources/people.json'))

    random.seed(seed)
    random.shuffle(people)

    return people


def sleep_if_needed(next_time):
    potential_sleep_time = next_time - datetime.datetime.now()

    if potential_sleep_time > datetime.timedelta(0):
        time.sleep(potential_sleep_time.total_seconds())

    return next_time + time_delay


def load_image(id):
    try:
        with open('resources/' + id + '.jpg', 'rb') as fp:
            return MIMEImage(fp.read())
    except FileNotFoundError:
        with open('resources/default.png', 'rb') as fp:
            return MIMEImage(fp.read())


if __name__ == '__main__':

    # random christmas tracks from spotify
    random_tracks = random_tracks('5OP7itTh52BMfZS1DJrdlv')

    # let user choose track from list
    track = choose_track(random_tracks)

    # load people from resources
    people = load_people(track['id'])

    # open track preview
    webbrowser.open(track['preview_url'])

    # ensure emails are sent out within playtime of preview
    delay = 30 / len(people)  # previews are 30 seconds long
    time_delay = datetime.timedelta(0, delay)
    next_time = datetime.datetime.now() + time_delay

    # send emails
    with smtplib.SMTP_SSL("smtp.gmail.com", os.getenv("SMTP_PORT"), context=ssl.create_default_context()) as server:

        server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))

        for idx, assailant in enumerate(people):
            next_time = sleep_if_needed(next_time)

            strFrom = os.getenv("SMTP_USERNAME")
            strTo = assailant['id'] + '@groundcontrol.com'

            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = 'Your Secret Santa'
            msgRoot['From'] = os.getenv("SMTP_USERNAME")
            msgRoot['To'] = strTo
            msgRoot.preamble = 'Multi-part message in MIME format.'

            msgAlternative = MIMEMultipart('alternative')
            msgRoot.attach(msgAlternative)

            victim = people[(idx + 1) % len(people)]

            msgText = MIMEText(
                'Your Secret Santa is <b>{victim}</b>.<br><br><img src="cid:headshot">'.format(victim=victim['name']),
                'html')
            msgAlternative.attach(msgText)

            msgImage = load_image(victim['id'])
            msgImage.add_header('Content-ID', '<headshot>')
            msgRoot.attach(msgImage)

            server.sendmail(strFrom, strTo, msgRoot.as_string())
            print('Sending random victim to {to}'.format(to=strTo))
