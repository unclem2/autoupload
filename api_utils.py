import requests
from bs4 import BeautifulSoup

base_url = "https://droidpp.osudroid.moe/api/ppboard"

class OsuAPI:
    def __init__(self, uid):
        self.base_url = "https://droidpp.osudroid.moe/api/ppboard"
        self.uid = uid

    def get_user_profile(self):
        url = self.base_url + "/getuserprofile"
        params = {"uid": self.uid}
       
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Response error: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Requests error: {e}")
            return None
        
# Live DPP/ osudroid.moe   
# UID-based
def get_user_info_from_first_site(uid):
        user_info_dict = {
            "UID": uid,
            "Местоположение": None,
            "Рейтинг (Rank)": None,
            "Никнейм": None,
            "Ranked Score": None,
            "Hit Accuracy": None,
            "Play Count": None,
        }

        print(f"Запрос информации для UID: {uid}")

        # Отправка GET-запроса к веб-сайту первого сайта
        url = "https://osudroid.moe/profile.php?uid=" + str(uid)
        response = requests.get(url)

        # Проверка статуса ответа и парсинг информации с первого сайта
        if response.status_code == 200:
            print("Запрос успешен.")
            soup = BeautifulSoup(response.content, "html.parser")
            text_content = soup.get_text()

            location_start = text_content.find("Location:")
            rank_start = text_content.find("Rank:")
            nickname_element = soup.select_one("html body main div nav div div div:nth-of-type(3) div:nth-of-type(1) a:nth-of-type(1)")

            if location_start != -1 and rank_start != -1:
                location = text_content[location_start + len("Location:"):].splitlines()[0].strip()
                rank = text_content[rank_start + len("Rank:"):].splitlines()[0].strip()

                user_info_dict["Местоположение"] = location
                user_info_dict["Рейтинг (Rank)"] = rank

            if nickname_element:
                nickname = nickname_element.text
                user_info_dict["Никнейм"] = nickname

            table = soup.find("table")
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        cell_label = cells[0].text.strip()
                        cell_value = cells[1].text.strip()
                        if cell_label in user_info_dict:
                            user_info_dict[cell_label] = cell_value

        else:
            print(f"Ошибка при запросе для UID {uid}:", response.status_code)

        return user_info_dict

def get_recent_plays(uid):

    url = f'https://osudroid.moe/profile.php?uid={uid}'
    # Создаем список для хранения результатов
    results = []
    mod_abbreviations = {
        'NoFail,': 'NF',
        'Easy,': 'EZ',
        'HalfTime,': 'HT',
        'Hidden,': 'HD',
        'HardRock,': 'HR',
        'DoubleTime,': 'DT',
        'Flashlight,': 'FL',
        'Precise,': 'PR',
        'SuddenDeath,': 'SD',
        'Perfect,': 'PF',
        'NoFail': 'NF',
        'Easy': 'EZ',
        'HalfTime': 'HT',
        'Hidden': 'HD',
        'HardRock': 'HR',
        'DoubleTime': 'DT',
        'Flashlight': 'FL',
        'Precise': 'PR',
        'SuddenDeath': 'SD',
        'Perfect': 'PF',
        'NightCore': 'NC',
        'NightCore,': 'NC'
        # Добавьте остальные модификаторы и их аббревиатуры
        # ААААААААААААААААААААААААААААААААААААААААА ЭТО ПИЗДЕЦ
    }
    # Отправляем GET-запрос на получение HTML-контента страницы
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        li_elements = soup.find_all('li', class_='li', style='margin-left: 15px; margin-right: 10px;')
        index = 1
        for li in li_elements:
            entry = {}
            
            entry['index'] = index
            index += 1


            img_element = li.find('img')
            if img_element:
                image_url = img_element['src']
                entry['rank'] = image_url
                entry['rank'] = entry['rank'].replace('../assets/img/ranking-', '').replace('.png', '')

            div = li.find('div', style='margin-bottom: 15px')
            if div:
                strong_element = div.find('strong')
                if strong_element:
                    entry['title'] = strong_element.get_text(strip=True)
                
                inner_div = div.find('div', style='margin: 0; color: black;')
                if inner_div:
                    small_element = inner_div.find('small', style='margin-left: 50px;')
                    if small_element:
                        details_lines = small_element.get_text(strip=True).split(' / ')
                        for detail in details_lines:
                            parts = detail.split(': ')
                            if len(parts) == 2:
                                key, value = parts
                                entry[key.strip()] = value.strip()
                                if 'combo' in entry:
                                    entry['combo'] = entry['combo'].replace(' x', '')
                                    if 'accuracy' in entry:
                                        entry['accuracy'] = entry['accuracy'].replace('%', '')
                        
                        small_miss_element = inner_div.find('small', style='color: #A82C2A;')
                        if small_miss_element:
                            miss = small_miss_element.get_text(strip=True).split(': ')[-1]
                            entry['miss'] = miss

                        span_element = inner_div.find('span', style='display:none;')
                        if span_element:
                            span_text = span_element.get_text(strip=True)
                            start_index = span_text.find(':') + 1
                            hash_value = span_text[start_index:].strip(' "{}')
                            entry['hash'] = hash_value

                            if 'mod' in entry:
                                mods = entry['mod'].split()
                                speed_multiplier = None
                                filtered_mods = []
                                for mod in mods:
                                    if mod.startswith('x'):
                                        speed_multiplier = mod[1:]
                                        entry['speedmultiplier'] = speed_multiplier
                                    else:
                                        filtered_mods.append(mod)
                                
                                entry['mod'] = ''.join([mod_abbreviations.get(mod, mod) for mod in filtered_mods])
                      
                    results.append(entry)
    else:
        print('Ошибка при запросе страницы')
    return results


def process_user_profile_data(user_profile_data):

        if user_profile_data:
            profile_data = {
                "uid": user_profile_data["uid"],
                "username": user_profile_data["username"],
                "Total PP": user_profile_data["pptotal"],
                "PP Rank": user_profile_data["pprank"],
                "DPP Playcount": user_profile_data["playc"]
            }
            return profile_data
        else:
            return None

def process_top_plays(user_profile_data):
        if user_profile_data:
            top_plays = []
            for map_data in user_profile_data["pp"]:
                play_info = {
                    "title": map_data["title"],
                    "hash": map_data["hash"],
                    "pp": map_data["pp"],
                    "mods": map_data["mods"],
                    "accuracy": map_data["accuracy"],
                    "combo": map_data["combo"],
                    "miss": map_data["miss"],
                    "speed_multiplier": map_data["speedMultiplier"],
                   
                   
                }
                top_plays.append(play_info)
            return top_plays
        else:
            return []  # Изменено с None на пустой список

# UID-less

def calculate_beatmap_pp(beatmaplink, mods, accuracy, combo, misses, speedmultiplier, forcear, forcecs, forceod):
                url = base_url + "/calculatebeatmap"
                data = {
                    "beatmaplink": beatmaplink,
                    "mods": mods,
                    "accuracy": accuracy,
                    "combo": combo,
                    "misses": misses,
                    "speedmultiplier": speedmultiplier,
                    "forcear": forcear,
                    "forcecs": forcecs,
                    "forceod": forceod,
                    
                }
                print(data)
                response = requests.post(url, data=data)

                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    return None

def fetch_leaderboard(page, query):
            url = base_url + "/getleaderboard"
            params = {
                "page": page,
                "query": query
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
                return []


# Rebalance DPP




def main():
    uid = input("Введите uid пользователя: ")
    api = OsuAPI(uid)
    user_profile_data = api.get_user_profile()

    if user_profile_data:
        profile_data = process_user_profile_data(user_profile_data)
        top_plays = process_top_plays(user_profile_data)
        recents = get_recent_plays(uid)

        print("User Profile Data:")
        print(profile_data)
        
        user_info_dict = get_user_info_from_first_site(uid)
        print("\nUser Info from First Site:")
        print(user_info_dict)
        
    

        print("\nRecent Plays:")
        print(recents)
    else:
        print("Ошибка при выполнении запроса")

if __name__ == "__main__":
    main()
