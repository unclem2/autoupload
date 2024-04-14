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


def get_bg(beatmapsetlink, diff_name):
    url = f"https://api.chimu.moe/v1/download/{beatmapsetlink}"
    response = requests.get(url)
    nf_path = "pluhan.jpg"
    if response.status_code == 200:
        zip_file = io.BytesIO(response.content)
        path = f"maps/{beatmapsetlink}"
        with zipfile.ZipFile(zip_file) as z:
            z.extractall(path)
            
            
    try:
        with open(f"maps/{beatmapsetlink}/{diff_name}", "r", encoding="utf-8") as osu_file:
            osu_content = osu_file.read()

            events_section = False
            background_event_found = False
            target_text = None

            for line in osu_content.splitlines():
                if line.startswith("[Events]"):
                    events_section = True
                    continue
                elif events_section and line.startswith("//Background and Video events"):
                    background_event_found = True
                    continue
                elif background_event_found and line:
                    elements = line.split(",")
                    if len(elements) >= 3:
                        target_text = elements[2].strip('"')
                        break

            if target_text:
                image_path = f"maps/{beatmapsetlink}/{target_text}"  # Путь к изображению
                print(image_path)
                try:
                    bg = image_path
                    return bg
                except FileNotFoundError:
                    print(f"Изображение '{target_text}' не найдено в папке")
                    return nf_path
            else:
                print("Информация о фоновом изображении не найдена")
                return nf_path
    except:
        print(f"Файл '{diff_name}' не найден в архиве")
        return nf_path
   

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


def generate_preview(uid, beatmaplink, play):
        api_key= ""    
    
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
        dpp_result = calculate_and_print_dpp(beatmaplink, mods, accuracy, misses, speedmultiplier, combo, play)
        print(dpp_result)
        beatmapid = dpp_result['beatmap']['id']
        osu_api_data = get_osu_api_data(beatmapid, api_key)
        beatmapsetlink = osu_api_data[0]['beatmapset_id']
        # Запрос к osudroid.moe
        odapi = get_user_info_from_first_site(uid)
        # Получение ДПП профиля
                    
        dppapi = OsuAPI(uid)
        user_profile_data = dppapi.get_user_profile()
        dppuserdata = process_user_profile_data(user_profile_data)
        diff_name = f"{osu_api_data[0]['artist']} - {osu_api_data[0]['title']} ({osu_api_data[0]['creator']}) [{osu_api_data[0]['version']}].osu"

        # Отладочный вывод
        print(odapi)
        print(dppuserdata)
        bg_data = get_bg(beatmapsetlink, diff_name)
        print(bg_data)
        generatedimage = generate_and_save_image(uid, play, dpp_result, osu_api_data, odapi, dppuserdata, bg_data, diff_name, mods, speedmultiplier)
        return generatedimage 
            
                   


def generate_image(data, bg_data, play, smdata):
    size = (1566, 710)
    image = Image.new("RGB", size, "black")
    draw = ImageDraw.Draw(image)

    # Открытие оверлея
    overlay_path = "overlay.png"
    overlay = Image.open(overlay_path)


    font = ImageFont.truetype("ttcommons.otf", 36)
    fontsmall = ImageFont.truetype("ttcommons.otf", 20)
# Основные позиции
    positions = {
    'uid': (50, 50),
    'nickname': (20, 384),
    'userdpp': (21, 429),
    'rank': (20,344),
    'dpp': (925, 570),
    'combo': (661, 474),
    'score': (661, 357),
    'acc': (987, 474),
    'title': (400, 36),
    'mods': (661, 570),
    'speed': (783, 628),
    'country': (60, 60),
    'miss': (1190, 570)
        # Добавьте здесь свои позиции для других переменных
    }
# Уменьшенные позиции
    smallpos = {
        'params': (1100, 112),
        'stars': (1480, 112),
        'mapper': (400, 112),
        'time': (29, 659)

    }
    
# ПНГшки рангов
    rank_images = {
    'D': Image.open("ranks/ranking-D.png"),
    'C': Image.open("ranks/ranking-C.png"),
    'B': Image.open("ranks/ranking-B.png"),
    'A': Image.open("ranks/ranking-A.png"),
    'S': Image.open("ranks/ranking-S.png"),
    'SH': Image.open("ranks/ranking-SH.png"),
    'X': Image.open("ranks/ranking-X.png"),
    'XH': Image.open("ranks/ranking-XH.png")
    }

    rank = play['mark'] 
    uid = data['uid']
    avatar_url = f"https://osudroid.moe/user/avatar/{uid}.png"

    try:
        response = requests.get(avatar_url)
        with open(f'{uid}.png', 'wb') as f:
            f.write(response.content)
        avatar = Image.open(f'{uid}.png')
    except:
        avatar = Image.open('pluhan.jpg')

    new_avatar_width = 310  
    new_avatar_height = 310  
    resized_avatar = avatar.resize((new_avatar_width, new_avatar_height), Image.LANCZOS)
    country_images = {
    'BY': Image.open("flags/Belarus.png"),  
    'UA': Image.open("flags/Ukraine.png"),
    'RU': Image.open("flags/Russia.png"),
    'KZ': Image.open("flags/Kazakhstan.png"),
    'AZ': Image.open("flags/Azerbaijan.png"),
    'CZ': Image.open("flags/Czech-Republic.png"),
    'LV': Image.open("flags/Latvia.png")
    }

    country = data['country']

    overlay_size = (1920, 710)  # Измените на размеры вашего оверлея
    overlay_position = (0, 0)  # Положение оверлея на изображении

    try:
        bg_path = bg_data
        background = Image.open(bg_path)
    except:
        nf_path = "pluhan.jpg"
        background = Image.open(nf_path)    

# Ресайз
    new_width = 1190
    new_height = 670
    resized_bg = background.resize((new_width, new_height), Image.LANCZOS)

# Наложите измененный фон на изображение
    image.paste(resized_bg, (350, 20))
    image.paste(overlay, overlay_position, overlay)


# Вставка рангов
    if rank in rank_images:
        rank_image = rank_images[rank]
        rank_image = rank_image.resize((142, 178))  # Укажите желаемые размеры
        mask = rank_image.split()[3]  # Извлекаем альфа-канал
        image.paste(rank_image, (436, 386), mask)
# Вставка стран
    if country in country_images:
        country_image = country_images[country]
        country_image = country_image.resize((32, 32))  # Укажите желаемые размеры
        maskc = country_image.split()[3]  # Извлекаем альфа-канал
        image.paste(country_image, (282, 344), maskc)
# Вставка обычного текста
    for key, value in data.items():
        if isinstance(value, dict):
            # draw.text(positions.get(key, (20, 20)), f"{key}:", font=font, fill="white")
            sub_positions = positions.get(f'{key}_sub', {})
            for sub_key, sub_value in value.items():
                sub_position = sub_positions.get(sub_key, (40, 40))
                draw.text(sub_position, f"{sub_value}", font=font, fill="white")
        else:
            draw.text(positions.get(key, (20, 20)), f"{value}", font=font, fill="white")

# Вставка мелкого текста

    for key, value in smdata.items():
        if isinstance(value, dict):
            # draw.text(positions.get(key, (20, 20)), f"{key}:", font=font, fill="white")
            sub_pos = smallpos.get(f'{key}_sub', {})
            for sub_key, sub_value in value.items():
                sub_posit = sub_pos.get(sub_key, (40, 40))
                draw.text(sub_posit, f"{sub_value}", font=fontsmall, fill="white")
        else:
            draw.text(smallpos.get(key, (20, 20)), f"{value}", font=fontsmall, fill="white")  

    image.paste(resized_avatar, (20, 20))    
    
    return image            

def generate_and_save_image(uid, play, dpp_result, osu_api_data, odapi, dppuserdata, bg_data, diff_name, mods, speedmultiplier): 
    # КТО ЖЕ СУКА ЗНАЛ ЧТО ПОРЯДОК ПЕРЕДАЧИ ПЕРЕМЕННЫХ НА ЧЕ ТО ВЛИЯЕТ СУКА КАКОЙ ЖЕ Я ДУРАК
    # Для понимания этой ХУЙНИ вставьте def generate_and_save_image(uid, play, osu_api_data, dpp_result): вместо 136 строки 
    # Вывести тип данных значения 'total'
    current_time = datetime.datetime.now()
    print(current_time)
         


    try:
        data = {
            'uid': uid,
            'rank': f"{odapi['Рейтинг (Rank)']} / # {dppuserdata['PP Rank']}",
            'nickname': odapi['Никнейм'],
            'userdpp': f"{round(dppuserdata['Total PP'], 2)} dpp",
            'dpp': f"{round(dpp_result['performance']['droid']['total'], 2)} dpp",
            'combo': f"{play['combo']}/{dpp_result['beatmap']['maxCombo']}x",
            'score': f"{play['score']}",
            'acc': f"{play['accuracy']}%",
            'country': f"{odapi['Местоположение']}",
            'title': f"{osu_api_data[0]['artist']} - {osu_api_data[0]['title']} [{osu_api_data[0]['version']}]",
            'mods': mods,
            'speed': speedmultiplier,
            'miss': f"{play['misses']}x"
                }
    except:
        data = {
        'uid': uid,
        'rank': f"{odapi['Рейтинг (Rank)']} / #None",
        'nickname': odapi['Никнейм'],
        'userdpp': "None dpp",
        'dpp': f"{round(dpp_result['performance']['droid']['total'], 2)} dpp",
        'combo': f"{play['combo']}/{dpp_result['beatmap']['maxCombo']}x",
        'score': f"{play['score']}",
        'acc': f"{play['accuracy']}%",
        'country': f"{odapi['Местоположение']}",
        'title': f"{osu_api_data[0]['artist']} - {osu_api_data[0]['title']} [{osu_api_data[0]['version']}]",
        'mods': mods,
        'speed': speedmultiplier,
        'miss': f"{play['misses']}x"
                }
    smdata = {
            'params': f"CS {round(dpp_result['beatmap']['modifiedStats']['cs'], 2)} ・ AR {round(dpp_result['beatmap']['modifiedStats']['ar'], 2)} ・ OD {round(dpp_result['beatmap']['modifiedStats']['od'], 2)} ・ HP {round(dpp_result['beatmap']['modifiedStats']['hp'], 2)}  ・ BPM {osu_api_data[0]['bpm']} ",
            'stars': f"{round(dpp_result['difficulty']['droid']['total'], 2)}",
            'mapper': f"mapped by {dpp_result['beatmap']['creator']}",
             'time': current_time
    }

    # Создаем изображение с настроенными позициями и текстом
    generated_image = generate_image(data, bg_data, play, smdata)
    
    # Создаем папку для сохранения изображений, если её еще нет
    output_folder = os.path.join(os.getcwd(), 'output_images')  # Имя папки можете изменить
    os.makedirs(output_folder, exist_ok=True)

    # Сохраняем изображение в файл в созданную папку
    vremya = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(output_folder, f"{vremya}-{uid}_generated.png")
    generated_image.save(output_path)
    return f"{output_folder}/{vremya}-{uid}_generated.png"
