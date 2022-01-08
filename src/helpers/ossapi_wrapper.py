from ossapi import OssapiV2
from helpers.config import Config

config = Config()

api = OssapiV2(client_id=int(config["OSU"]["client_id"]), client_secret=config["OSU"]["client_secret"])
