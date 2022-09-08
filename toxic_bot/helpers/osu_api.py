import asyncio
import logging
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import List, Dict, Optional, Union, Any

import aiohttp
from multidict import CIMultiDict

logger = logging.getLogger('toxic-bot')


class OsuApiV2(aiohttp.ClientSession):
    """
    Async wrapper for osu! api v2
    """

    def __init__(self, client_id: str, client_secret: str, osu_session_key: str):
        super(OsuApiV2, self).__init__()
        self._default_headers = CIMultiDict()
        self._osu_client_id = client_id
        self._osu_session_key = osu_session_key
        self._osu_client_secret = client_secret
        self._osu_api_base_url = 'https://osu.ppy.sh/api/v2/'

        self._osu_access_token = None
        self._access_token_obtain_date = None
        self._access_token_expire_date = None

        self._osu_api_cooldown = 1
        self._last_request_time = datetime.now() - timedelta(seconds=self._osu_api_cooldown)

        return

    async def get_user_beatmap_score(self, user_id: int, beatmap_id: int, mode: str = "osu"):
        """
        Gets the score for the specified user and beatmap.
        :param user_id: The ID of the user.
        :param beatmap_id: The ID of the beatmap.
        :param mode: Game mode. One of [fruits, mania, osu, taiko]
        :return: Returns Score object.
        """
        logger.debug(f'Requesting user score for id: {user_id} and beatmap id: {beatmap_id}')
        return await self._get_endpoint(f'beatmaps/{beatmap_id}/scores/users/{user_id}')

    async def get_user_scores(self,
                              user_id: int,
                              score_type: str,
                              limit: int = 50,
                              include_fails: Optional[int] = None,
                              mode: Optional[str] = None,
                              offset: Optional[int] = None) -> List[SimpleNamespace]:
        """
        This endpoint returns the scores of specified user.
        :param user_id: User id.
        :param score_type: Score type. Must be one of these: best, firsts, recent.
        :param limit: Maximum number of results.
        :param include_fails: Only for recent scores, include scores of failed plays. Set to 1 to include them. Defaults to 0.
        :param mode: GameMode of the scores to be returned. Defaults to the specified user's mode.
        :param offset: Result offset for pagination.
        :return: Array of Scores.
        """
        params = {"include_fails": include_fails, "mode": mode, "limit": limit,
                  "offset": offset}
        logger.debug(f'Requesting user {score_type} ranks with {params}')
        return await self._get_endpoint(f'users/{user_id}/scores/{score_type}', params)

    async def get_country_beatmap_scores(self, beatmap_id: int):
        """
        Retrieves the Turkish country leaderboard for the specified beatmap ID.
        :param beatmap_id: The ID of the beatmap.

        :return: Returns multiple score objects
        """
        params = {
            "type": "country",
            "mode": "osu",
        }
        header = {
            'cookie': f'osu_session={self._osu_session_key}',
        }
        logger.debug(f'Requesting country ranks with {params}')

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://osu.ppy.sh/beatmaps/{beatmap_id}/scores",
                                   params=params,
                                   headers=header) as country_rsp:
                country_content = await country_rsp.json()

        return self._format_response(country_content["scores"])

    async def get_country_top_50(self, country_code: str, game_mode: str = 'osu'):
        """
        Gets the current ranking for the specified type and game mode.
        :param country_code: Filter ranking by country code.
        :param game_mode: Game mode. One of [fruits, mania, osu, taiko]
        :return: Returns Rankings
        """
        params = {'country': country_code}
        logger.debug(f'Requesting country top player list with {params}')
        return await self._get_endpoint(f'rankings/{game_mode}/performance', params)

    async def get_beatmap(self, beatmap_id: int):
        """
        Gets beatmap data for the specified beatmap ID.
        :param beatmap_id: The ID of the beatmap.
        :return: Returns Beatmap object.

        This endpoint returns a single beatmap object.
        """
        logger.debug(f'Requesting beatmap information for id: {beatmap_id}')
        return await self._get_endpoint(f'beatmaps/{beatmap_id}')

    async def get_user(self, user_id: Union[str, int], game_mode: Optional[str] = None,
                       key: Optional[str] = 'id') -> SimpleNamespace:
        """
        This endpoint returns the detail of specified user.
        It's highly recommended to pass key parameter to avoid getting unexpected result
        (mainly when looking up user with numeric username or nonexistent user id).
        :param user_id: Id or username of the user.
        :param key: Type of user passed in url parameter.
                    Can be either id or username to limit lookup by their respective type.
                    Passing empty or invalid value will result in id lookup followed by username lookup if not found.
        :param game_mode: GameMode. User default mode will be used if not specified.
        :return:
        """

        logger.debug(f'Requesting user information for user: {user_id}')
        params = {'key': key}
        endpoint = f'users/{user_id}/{game_mode}' if game_mode else f'users/{user_id}'
        return await self._get_endpoint(endpoint=endpoint, params=params)

    async def get_beatmap_bytes(self, beatmap_id: int):
        """
        Gets the beatmap bytes from osu! http endpoint. THIS IS NOT AN API CALL.
        :param beatmap_id: Id of the beatmap.
        :return:
        """
        logger.debug(f'Requesting beatmap bytes for id: {beatmap_id}')
        async with aiohttp.ClientSession() as c:
            async with c.get(f'https://osu.ppy.sh/osu/{beatmap_id}') as resp:
                contents = await resp.read()
        return contents

    async def _get_endpoint(self, endpoint: str, params: dict = None) -> Union[List, SimpleNamespace]:
        params = self._format_params(params)
        if self._osu_access_token is None or await self._check_token_expired():
            await self._get_access_token()

        seconds_since_last_request = (datetime.now() - self._last_request_time).total_seconds()
        if seconds_since_last_request < self._osu_api_cooldown:
            await asyncio.sleep(self._osu_api_cooldown - seconds_since_last_request)

        async with self.get(f'{self._osu_api_base_url}{endpoint}', params=params) as resp:
            contents = await resp.json()

        self._last_request_time = datetime.now()

        return self._format_response(contents)

    def _format_response(self, response: Union[List, Dict]) -> Union[List, SimpleNamespace, Any]:
        if 'error' in response:
            return None
        if isinstance(response, list):
            return [self._format_dict(r) for r in response]
        elif isinstance(response, dict):
            return self._format_dict(response)

    def _format_dict(self, d: dict) -> SimpleNamespace:
        new_dict = {}
        for key, value in d.items():
            if isinstance(value, dict):
                new_dict[key] = self._format_dict(value)
            else:
                new_dict[key] = value
        else:
            return SimpleNamespace(**new_dict)

    @staticmethod
    def _format_params(params: Optional[dict]) -> dict:
        if params is None:
            return {}
        keys_to_pop = []
        for key, value in params.items():
            if value is None:
                keys_to_pop.append(key)
        [params.pop(key) for key in keys_to_pop]
        return params

    async def _get_access_token(self):
        params = {'client_id': self._osu_client_id,
                  'client_secret': self._osu_client_secret,
                  'grant_type': 'client_credentials',
                  'scope': 'public'}

        async with aiohttp.ClientSession() as c:
            async with c.post('https://osu.ppy.sh/oauth/token', json=params) as r:
                token_response = await r.json()

        self._osu_access_token = token_response['access_token']
        self._access_token_obtain_date = datetime.now()
        self._access_token_expire_date = self._access_token_obtain_date + timedelta(
            seconds=token_response['expires_in'])

        self._default_headers = CIMultiDict({'Authorization': f'Bearer {self._osu_access_token}'})

    async def _check_token_expired(self):
        return datetime.now() + timedelta(seconds=100) > self._access_token_expire_date
