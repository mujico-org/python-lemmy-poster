#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Takes the last 10 user tweets and posts them to Reddit if they include one image."""

import requests
import tweepy
from datetime import datetime, timezone
from datetime import timedelta

import config

CONSUMER_KEY = config.CONSUMER_KEY

CONSUMER_SECRET = config.CONSUMER_SECRET

ACCESS_TOKEN = config.ACCESS_TOKEN

ACCESS_TOKEN_SECRET = config.ACCESS_TOKEN_SECRET

# La URL base
BASE = config.BASE

# URL para iniciar sesión
LOGIN = config.LOGIN

# URL para crear post
CREATE_POST = config.CREATE_POST

# URL para subir imagen al servidor
UPLOAD_IMAGE = config.UPLOAD_IMAGE

# Usuario y contraseña de la cuenta
USERNAME = config.USERNAME
PASSWORD = config.PASSWORD

LOG_FILE='./processed_tweets.txt'


def load_file(file):
    """Load the log file and creates it if it doesn't exist.

     Parameters
    ----------
    file : str
        The file to write down
    Returns
    -------
    list
        A list of urls.
    """

    try:
        with open(file, 'r', encoding='utf-8') as temp_file:
            return temp_file.read().splitlines()
    except Exception:

        with open(LOG_FILE, 'w', encoding='utf-8') as temp_file:
            return []


def update_file(file, data):
    """Update the log file.

    Parameters
    ----------
    file : str
        The file to write down.
    data : str
        The data to log.
    """

    with open(file, 'a', encoding='utf-8') as temp_file:
        temp_file.write(data + '\n')


def get_tweets(api, t_user):
    """Get tweets from api.

    Parameters
    ----------
    api : tweepy.API
        twitter api object
    t_user : str
        The username of twitter you want to get.

    Returns
    -------
    list
        A list of tweets.

    """

    # test authentication

    try:
        api.verify_credentials()
        print('Authentication OK')
    except Exception as e:
        print(str(e))
        print('Error during authentication')
        exit()
    user = api.get_user(screen_name=t_user)
    tweets = api.user_timeline(screen_name=user.screen_name, count=10,
                               include_rts=False, exclude_replies=True,
                               tweet_mode='extended')
    return tweets[:10]


def lemmy_loging():
    """
    Esta función inicia sesión y devuelve un JWT.
    """

    data = {
        "username_or_email": USERNAME,
        "password": PASSWORD
    }

    with requests.post(BASE + LOGIN, json=data) as response:
        return response.json()["jwt"]


def lemmy_upload_picture(token, image_path):
    """
    Esta función sube una imagen al servidor y devuelve
    la URL donde está almacenada.
    """

    headers = {
        "Cookie": f"jwt={token}"
    }

    files = {"images[]": open(image_path, "rb")}

    with requests.post(UPLOAD_IMAGE, headers=headers, files=files) as response:
        # print(response.status_code)
        # print(response.text)
        return response.json()["files"][0]["file"]


def lemmy_create_post(token, title, community =5 , url = BASE):
    """
    Esta función crea el post en la comunidad específicada.

    El id de la comunidad es un número, para conocerlo debes buscarlo aquí:

    https://soranos.app/api/v3/community/list

    """

    data = {
        "name": title,
        "community_id": community,
        "auth": token,
        "url": url
    }

    with requests.post(BASE + CREATE_POST, json=data) as response:
        print(response.status_code)


def init_bot():
    """Read twwts get images and submit to subreddit."""

    # We create the Lemmy instance.


    # Authenticate to Twitter

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    # Create API object

    api = tweepy.API(auth, wait_on_rate_limit=True)

    tweets = get_tweets(api, 'iMemeflixx')

    # Datetime tolerance, set to 4 hours

    tolerance_time = datetime.now(timezone.utc) - timedelta(hours=4)

    print(tolerance_time)

    log = load_file(LOG_FILE)
    
    # Primero obtenemos el JWT
    token = lemmy_loging()

    for tweet in reversed(tweets):
        try:
            image_count = len(tweet.extended_entities['media'])
            print('media number: {}  created_at: {}'.format(
                image_count, tweet.created_at))
            if image_count and image_count < 2 and tweet.created_at >= tolerance_time or True:
                print("loo")
                title = ' '.join([item for item in tweet.full_text.split(
                    ' ') if 'https' not in item]).replace('.', '')
                title = ' '.join(title.replace(
                    '\r', '. ').replace('\n', '. ').split())

                if title in log:
                    continue

                lemmy_create_post(
                    token,
                    title,
                    5,
                    tweet.entities['media'][0]['media_url']
                )


                update_file(LOG_FILE, title)
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':

    init_bot()
