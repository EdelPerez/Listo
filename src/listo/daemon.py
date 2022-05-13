import re
import sys
import time
import requests
from .exception import APIFail, NoReleasingAnime
from datetime import datetime, timedelta


class Listo(object):
    """A simple Discord bot that monitors AniList.co for all upcoming anime
    releasing in the next 24 hours (TV, OVA, ONA, ext).

    Args:
        webhook (str): Discord webhook url.
    """
    def __init__(self, webhook: str='', allow_all_anime=False, allow_hentai=False, verbose=False) -> None:
        self._webhook = webhook
        self._allow_all_anime = allow_all_anime
        self._allow_hentai = allow_hentai
        self._verbose = verbose

    @staticmethod
    def _format_description(description: str) -> str:
        """Format the description.

        Args:
            description (str): Description from AniList

        Returns:
            str: Formated description.
        """

        # remove any HTML tag
        CLEAR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

        if description and len(description) > 150:
            return f"{re.sub(CLEAR, '', description)[:150]}..."
        elif description:
            return re.sub(CLEAR, '', description)

        return 'This anime has no description...\t¯\_(ツ)_/¯'

    def _process_response(self, response: list) -> list:
        """Process the response from AniList. The data is cleaned and added to 
        a new list (every anime is represented by dictionary).

        Args:
            response (list): Releasing anime gather from AniList

        Returns:
            list: Clean list of releasing anime from AniList.
        """

        anime_list = []
        
        for anime in response:
            hentai = self._allow_hentai or not anime['media']['isAdult']
            country = self._allow_all_anime or anime['media']['countryOfOrigin'] == 'JP'
            
            if hentai and country:
                studio = anime['media']['studios']['nodes']
                
                anime_list.append(
                    {
                        'title': anime['media']['title']['romaji'],
                        'airingAt': datetime.fromtimestamp(anime['airingAt']),
                        'episode': anime['episode'],
                        'coverImage': f"https://img.anili.st/media/{anime['media']['id']}",
                        'description': self._format_description(anime['media']['description']),
                        'studio': studio[0]['name'] if studio else 'N/A',
                        'aniLink': f"https://anilist.co/anime/{anime['media']['id']}",
                    }
                )

        if self._verbose:
            print(f"{len(anime_list)} episode(s) releasing in the next 24 hours")
        
        return anime_list

    def _get_releasing_anime(self, start_time: int, end_time: int) -> list:
        """Gets a list of releasing anime from AniList.co.

        Args:
            start_time (int): Integer representation of unix datetime.
            end_time (int): Integer representation of unix datetime.

        Raises:
            APIFail: Raises when API call fails from http code 500 or higher.
            NoReleasingAnime: Raises when API returns a http 404 error code (No
            anime found on AniList)

        Returns:
            list: List of releasing anime.
        """
        query = '''
            query ($start: Int, $end: Int)  {
                Page(perPage: 50) {
                pageInfo {
                    total
                }
                airingSchedules(airingAt_greater: $start, airingAt_lesser: $end, sort: TIME) {
                    episode
                    airingAt
                    media {
                        id
                        isAdult
                        countryOfOrigin
                        title {
                            romaji
                        }
                        description
                        studios(isMain: true) {
                            nodes {
                            name
                            }
                        }
                    }
                }
                }
            }
            '''
        
        variables = {
            'start': start_time,
            'end': end_time
        }

        if self._verbose:
            print('Contacting AniList servers')
        
        r = requests.post(url='https://graphql.anilist.co', json={'query': query, 'variables': variables})
        
        if not r.ok:
            raise APIFail(f'ERROR: AniList API call failed with code {r.status_code}')
        
        if r.status_code == 404:
            raise NoReleasingAnime("WARNING: No new episode found for the next 24 hours.")
        
        anime = r.json() 
        response = anime['data']['Page']['airingSchedules']

        if self._verbose:
            print('Successfully established a connection. Processing response')

        return self._process_response(response)
    
    def _post_to_discord(self, anime: dict) -> None:
        """Post the currently releasing anime to Discord.

        Args:
            anime (dict): Releasing anime.

        Raises:
            APIFail: Raise if Discord API call fails with http error code higher
            than 400.
        """
        hook = {
            "embeds": [
                {
                "title": anime['title'],
                "description": anime['description'],
                "url": anime['aniLink'],
                "color": 16734296,
                "fields": [
                    {
                    "name": "Episode",
                    "value": anime['episode'],
                    "inline": 'true'
                    },
                    {
                    "name": "Released",
                    "value": anime['airingAt'].strftime("%A @ %I:%M %p"),
                    "inline": 'true'
                    },
                    {
                    "name": "Studio",
                    "value": anime['studio'],
                    "inline": 'true'
                    }
                ],
                "image": {
                    "url": anime['coverImage']
                    }
                }
            ]
        }

        r = requests.post(url=self._webhook, json=hook)
            
        if not r.ok:
            raise APIFail(f'ERROR: Discord API call failed with code {r.status_code}')
            
        time.sleep(1)

        if not int(r.headers['X-RateLimit-Remaining']):
            seconds_to_retry = int(r.headers.get('X-RateLimit-Reset-After', '30'))
            
            print(f'WARNING: Discord API limit reached. Sleeping for {seconds_to_retry} seconds.')
            
            time.sleep(seconds_to_retry)

        if self._verbose:
            print('Success')

    def run(self) -> None:
        """Run the application."""

        start_time = datetime.now()     # On App run, set to the current time.

        while True:
            end_time = start_time + timedelta(hours=24)
            print(f'Checking for new releases: {start_time} to {end_time}')

            try:
                anime_list = self._get_releasing_anime(int(start_time.timestamp()), int(end_time.timestamp()))
            except (APIFail, NoReleasingAnime, KeyError, TimeoutError) as e:
                print(e, 'Retrying in 60 seconds.', sep='\n')
                time.sleep(60)
                continue
            except Exception as e:
                print(f'CRITICAL ERROR: {e}', '<-- Clossing App -->', sep='\n')
                sys.exit(1)
            
            for anime in anime_list:
                if anime['airingAt'] > datetime.now():
                    releasing_in = (anime['airingAt'] - datetime.now()).seconds
                    print(f'Waiting for next release(s) at {anime["airingAt"].strftime("%I:%M %p")}')
                    time.sleep(releasing_in)
                
                if self._verbose:
                    print(f'{anime["title"]} releasing. Posting to Discord')

                try:
                    self._post_to_discord(anime)
                except (APIFail, TimeoutError) as e:
                    print(e, 'Retrying in 30 seconds.', sep='\n')
                    start_time = anime['airingAt'] - timedelta(seconds=1)
                    time.sleep(30)
                    break
                except Exception as e:
                    print(f'CRITICAL ERROR: {e}', '<-- Clossing App -->', sep='\n')
                    sys.exit(1)
            else:
                if self._verbose:
                    print('Checking for new releases in the next 24 hours')
                
                start_time = datetime.now()