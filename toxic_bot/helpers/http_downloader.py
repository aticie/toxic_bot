import os
from urllib.parse import urlparse

import aiohttp


async def download_and_save_asset(url) -> str:
    """
    Downloads image from url and returns PIL Image
    """
    url_path = urlparse(url).path
    folder_name, filename = os.path.split(url_path)
    local_folder_path = os.path.join('assets', f'.{folder_name}')
    asset_file_path = os.path.join(local_folder_path, filename)
    os.makedirs(local_folder_path, exist_ok=True)

    if os.path.exists(asset_file_path):
        return asset_file_path

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response_bytes = await resp.read()

    with open(asset_file_path, "wb") as f:
        f.write(response_bytes)

    return asset_file_path


async def download_and_save_beatmap(beatmap_id) -> str:
    beatmap_download_url = f"https://osu.ppy.sh/osu/{beatmap_id}"
    return await download_and_save_asset(beatmap_download_url)