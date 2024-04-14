import gspread
from oauth2client.service_account import ServiceAccountCredentials
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
import json
import os
import time
import zipfile
import re
from genbg import generate_preview
from gendesc import generate_description
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def authorize_google_sheets(credentials_file, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def download_file_from_drive(file_id, filename, credentials_file, download_folder):
    # Создаем папку, если она не существует
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    # Путь к файлу внутри папки
    filepath = os.path.join(download_folder, filename)

    # Авторизация с помощью учетных данных
    creds = service_account.Credentials.from_service_account_file(credentials_file)
    drive_service = build('drive', 'v3', credentials=creds)

    # Загрузка файла по его идентификатору
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(filepath, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Прогресс загрузки файла {filename}: {int(status.progress() * 100)}%")

    print(f"Файл {filename} успешно загружен с Google Диска и сохранен в папке {download_folder}.")

def authenticate_youtube():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    if os.path.exists(TOKEN_PICKLE_FILE):
            with open(TOKEN_PICKLE_FILE, 'rb') as token:
                creds = pickle.load(token)

    # Если учетные данные не загружены или они устарели, запустите процесс авторизации
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        # Сохранение учетных данных для будущего использования
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def upload_video_to_youtube(video_path, preview_path, description, credentials, chunk_size=1024*1024):
    # Авторизация
    youtube = build('youtube', 'v3', credentials=credentials)

    # Устанавливаем описание и теги для видео
    request_body = {
        'snippet': {
            'title': 'Название вашего видео',
            'description': description,
            'tags': ['тег1', 'тег2', 'тег3']
        },
        'status': {
            'privacyStatus': 'public'  # Может быть также 'private' или 'unlisted'
        }
    }

    # Создаем запрос на загрузку видео
    media = MediaIoBaseUpload(video_path, mimetype='video/*', chunksize=chunk_size, resumable=True)
    insert_request = youtube.videos().insert(
        part=",".join(request_body.keys()),
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            print(f"Прогресс загрузки: {int(status.progress() * 100)}%")

    video_id = response['id']

    # Устанавливаем превью для видео
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=preview_path
    ).execute()

    print(f"Видео успешно загружено на YouTube. ID видео: {video_id}")

def update_json_file(json_file, datet, url):
    data = {'files': []}

    # Проверяем, существует ли файл JSON
    if os.path.exists(json_file):
        # Если файл существует, загружаем его содержимое
        with open(json_file, 'r') as f:
            data = json.load(f)

    # Добавляем новую запись в список файлов
    data['files'].append({'datet': datet, 'url': url})

    # Записываем данные обратно в JSON-файл с отступами для красивого форматирования
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def extract_entry_json(archive_filename):
    # Имя файла entry.json внутри архива
    entry_json_filename = "entry.json"

    try:
        # Открываем архив для чтения
        with zipfile.ZipFile(archive_filename, 'r') as zip_ref:
            # Извлекаем файл entry.json из архива во временную директорию
            zip_ref.extract(entry_json_filename)
        
        # Открываем файл entry.json для чтения
        with open(entry_json_filename, 'r') as f:
            # Читаем содержимое файла entry.json
            entry_data = json.load(f)
            replaydata = entry_data['replaydata']

            # Словарь для сопоставления коротких кодов модификаторов с описаниями
            mods_dict = {
                "|": "",
                "x": "RX",
                "p": "AP",
                "e": "EZ",
                "n": "NF",
                "r": "HR",
                "h": "HD",
                "i": "FL",
                "d": "DT",
                "c": "NC",
                "t": "HT",
                "s": "PR",
                "u": "SD",
                "f": "PF",
                "l": "RE",
            }

            # Получаем список модификаторов
            mods_list = replaydata['mod'].split("|")
            mod_descriptions = []

            ar_values = []
            cs_values = []
            hp_values = []
            od_values = []
            other_modifiers = []
            speed_multiplier = None

            for mod_item in mods_list:
                # Если модификатор содержит значение AR, CS, HP, OD или speed multiplier, добавляем его в соответствующий список
                if re.match(r'(AR|CS|HP|OD)\d+(\.\d+)?', mod_item):
                    mod_code = mod_item[:2]  # Получаем код модификатора (например, "AR", "CS", "HP" или "OD")
                    mod_value = re.search(r'\d+(\.\d+)?', mod_item).group()  # Получаем числовое значение модификатора
                    if mod_code == "AR":
                        ar_values.append(float(mod_value))  # Преобразуем строку в число и добавляем в список
                    elif mod_code == "CS":
                        cs_values.append(float(mod_value))
                    elif mod_code == "HP":
                        hp_values.append(float(mod_value))
                    elif mod_code == "OD":
                        od_values.append(float(mod_value))
                elif mod_item.startswith("x") and re.match(r'x\d+(\.\d+)?', mod_item):
                    # Если это speed multiplier, добавляем его в отдельную переменную
                    speed_multiplier = float(re.search(r'x(\d+(\.\d+)?)', mod_item).group(1))
                else:
                    # Если это другой модификатор, разделяем его на буквы и добавляем в общий список
                    other_modifiers.extend(list(mod_item))

            # Создаем отдельные строки в словаре для значений AR, CS, HP и OD
            replay_dict = {}
            replay_dict["AR"] = ""
            replay_dict["CS"] = ""
            replay_dict["OD"] = ""
            replay_dict["HP"] = ""
            if ar_values:
                replay_dict["AR"] = ar_values
            if cs_values:
                replay_dict["CS"] = cs_values
            if hp_values:
                replay_dict["HP"] = hp_values
            if od_values:
                replay_dict["OD"] = od_values

            # Добавляем описания модификаторов в словарь
            mod_descriptions = [mods_dict.get(mod_code, mod_code) for mod_code in other_modifiers]
            replay_dict["mod"] = mod_descriptions

            # Прогоняем описания модификаторов через словарь
            mod_descriptions = [mods_dict.get(mod, mod) for mod in mod_descriptions]


            # Объединяем все модификаторы в одну строку без разделителя
            mod_string = "".join(mod_descriptions)
            replay_dict["mod"] = mod_string
            # Добавляем speed_multiplier, если он определен
            if speed_multiplier is not None:
                replay_dict["speed_multiplier"] = speed_multiplier

            # Добавляем остальные данные в словарь
            replay_dict.update({
                "filename": replaydata['filename'],
                "playername": replaydata['playername'],
                "replayfile": replaydata['replayfile'],
                "score": replaydata['score'],
                "combo": replaydata['combo'],
                "mark": replaydata['mark'],
                "h300k": replaydata['h300k'],
                "h300": replaydata['h300'],
                "h100k": replaydata['h100k'],
                "h100": replaydata['h100'],
                "h50": replaydata['h50'],
                "misses": replaydata['misses'],
                "accuracy": replaydata['accuracy'] * 100,
                "time": replaydata['time'],
                "perfect": replaydata['perfect']
            })

            return replay_dict

    except Exception as e:
        print(f"Ошибка при извлечении или чтении файла entry.json: {e}")
        return None

def extract_file_id_from_url(url):
    # Паттерн для извлечения идентификатора файла из ссылки Google Диска
    pattern = r"/open\?id=([a-zA-Z0-9_-]+)"

    # Поиск идентификатора файла в ссылке с помощью регулярного выражения
    match = re.search(pattern, url)

    # Если найдено совпадение, извлекаем идентификатор файла
    if match:
        return match.group(1)
    else:
        print("Идентификатор файла не найден в данной ссылке.")
        return None

def check_and_download_new_files(sheet, credentials_file, json_file, download_folder):
    previous_num_rows = 0

    # Проверяем, существует ли файл JSON
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            downloaded_files = json.load(f)['files']
    else:
        downloaded_files = []

    while True:
        num_rows = len(sheet.get_all_values())

        if num_rows > previous_num_rows:
            print("Есть новые ответы!")
            new_responses = sheet.get_all_values()[previous_num_rows:]

            for i, response in enumerate(new_responses, start=previous_num_rows + 1):
                datet = response[0]
                url_video = response[1]
                url_archive = response[2]
                uid = response[3]
                beatmaplink = response[4]

                # Проверяем, был ли файл уже загружен
                if url_video not in [file['url'] for file in downloaded_files]:
                    file_id = extract_file_id_from_url(url_video)
                    if file_id:
                        filename = f"video_{i}.mp4"
                        download_file_from_drive(file_id, filename, credentials_file, download_folder)
                        update_json_file(json_file, datet, url_video)

                if url_archive not in [file['url'] for file in downloaded_files]:
                    file_id = extract_file_id_from_url(url_archive)
                    if file_id:
                        archive_filename = f"archive_{i}.zip"
                        download_file_from_drive(file_id, archive_filename, credentials_file, download_folder)
                        update_json_file(json_file, datet, url_archive)

                        # Извлекаем и читаем файл entry.json из архива
                        entry_json_data = extract_entry_json(os.path.join(download_folder, archive_filename))
                        if entry_json_data:
                            print(json.dumps(entry_json_data, indent=4))
                            preview = generate_preview(uid, beatmaplink, entry_json_data)
                            description = generate_description(uid, beatmaplink, entry_json_data)
                            video_path = os.path.join(download_folder, filename)
                            preview_path = preview
                            credentials = authenticate_youtube() # Запускаем процесс аутентификации для YouTube
                            upload_video_to_youtube(video_path, preview_path, description, credentials)

        else:
            print("Нет новых ответов.")

        previous_num_rows = num_rows
        time.sleep(10)

# Использование функций
sheet = authorize_google_sheets('credentials.json', 'Untitled form (Responses)')
download_folder = 'downloads'
check_and_download_new_files(sheet, 'credentials.json', 'data.json', download_folder)
