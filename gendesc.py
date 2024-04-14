from api_utils import get_recent_plays, calculate_beatmap_pp, get_user_info_from_first_site, process_user_profile_data, OsuAPI
import requests
import io
import zipfile
from PIL import Image, ImageDraw, ImageFont
import datetime
import os



def get_osu_api_data(beatmapid, api_key):
    api_url = f'https://osu.ppy.sh/api/get_beatmaps'
    params = {
        'k': api_key,
        'b': beatmapid
    }

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None  # Ошибка при запросе к osu! API



def calculate_and_print_dpp(beatmaplink, mods, accuracy, misses, speedmultiplier, combo, play):
    # Здесь вы можете использовать значения mods, accuracy и misses, как вам нужно
    # Замените эту строку на фактический вызов calculate_beatmap_pp с аргументами из osu! API
    # if not play['AR']:
    #     forcear = ""
    # else:
    #     forcear = play['AR'][0]    
    # if not play['OD']:
    #     forceod = ""
    # else:
    #     forceod = play['OD'][0]    
    # if not play['CS']:
    #     forcecs = ""
    # else:
    #     forcecs = play['CS'][0]   
    forcear= ""
    forceod= ""
    forcecs= ""  
  
    
    dpp_result = calculate_beatmap_pp(beatmaplink, mods, accuracy, combo, misses, speedmultiplier, forcear, forcecs, forceod)
    print(f"DPP для карты: {dpp_result}")
    return dpp_result


def generate_description(uid, beatmaplink, play):
        api_key= ""    
        # Переопределение
        try:
            mods = play['mod']
        except:
            mods = ''
        accuracy = play['accuracy'] 
        misses = play['misses']
        try:
            speedmultiplier = play['speed_multiplier']
        except:
            speedmultiplier = ''
        combo = play['combo']

        # Данные карты по дпп
        dpp_result = calculate_and_print_dpp(beatmaplink, mods, accuracy, misses, speedmultiplier, combo, play)
        # Данные карты по банчо
        beatmapid = dpp_result['beatmap']['id']
        osu_api_data = get_osu_api_data(beatmapid, api_key)
        # Данные акка дроида
        odapi = get_user_info_from_first_site(uid) 
        dppapi = OsuAPI(uid)
        user_profile_data = dppapi.get_user_profile()
        dppuserdata = process_user_profile_data(user_profile_data)

        description = "👇 Open the description for more information 👇\n\nAll copyrights belong to their legal representatives and fall under fair use"
        description += "// = Player links\n\n"
        description += f"Profile: https://osudroid.moe/profile.php?uid={uid}\nDPP profile: https://droidpp.osudroid.moe/profile/{uid}\nSkin: Soon\n\n"
        description += "// = Beatmap info\n\n"
        description += f"Link: https://osu.ppy.sh/b/{beatmapid}\n"
        description += f"Mapper: https://osu.ppy.sh/u/{osu_api_data[0]['creator_id']}\n\n"
        # TODO round fix
        description += f"std:\n {osu_api_data[0]['difficultyrating']}⭐ | {osu_api_data[0]['bpm']}bpm | AR: {osu_api_data[0]['diff_approach']} | CS: {osu_api_data[0]['diff_size']} | OD: {osu_api_data[0]['diff_overall']} | HP: {osu_api_data[0]['diff_drain']}\n"
        description += f"droid modified:\n {round(dpp_result['difficulty']['droid']['total'], 2)}⭐ | {osu_api_data[0]['bpm']}bpm | AR: {round(dpp_result['beatmap']['modifiedStats']['ar'], 2)} | CS: {round(dpp_result['beatmap']['modifiedStats']['cs'], 2)}  | OD: {round(dpp_result['beatmap']['modifiedStats']['od'], 2)} | HP: {round(dpp_result['beatmap']['modifiedStats']['hp'], 2)}\n\n"
        description += "// = Player info\n\n"
        description += f"Playcount: {odapi['Play Count']}\nRank: {odapi['Рейтинг (Rank)']} ({dppuserdata['PP Rank']})\nScore: {odapi['Ranked Score']}\nDPP: {round(dppuserdata['Total PP'], 2)}\n"
        # TODO score info
        description += f"playinfo later im tired\n"
        description += "// = Useful links\n\n"
        description += "osu!droid: https://osudroid.moe \nosu!droid discord server: https://discord.gg/osudroid.moe \nDPP Project: https://droidpp.osudroid.moe \n"
        description += "Source code: Soon\n"
        description += "// = What needs to be mentioned\n\n"
        description += "osu! is a free to play online rhythm game, which you can use as a rhythm trainer online with lots of gameplay music! https://osu.ppy.sh/ \n Description template copypasted from cpol channel.\nPreview template was made by Naren.\nEvetything code-related was made by unclem.\nPreview, description, name of video was generated automatically, there may be inaccuracies."
        return description
