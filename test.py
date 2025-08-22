import json
import urllib.request
import base64
import datetime
import sys
import uuid
import time

# Переменные для подключения к Nexus
NEXUS_URL = "http://192.168.13.62:8081"
API_URL = f"{NEXUS_URL}/service/rest/v1/search"
REPO_COMPONENT_NAME = "test"
REPO_COMPONENT_GROUP = "test"

# Учетные данные для базовой аутентификации
NEXUS_USER = "admin"
NEXUS_PASS = "admin"

# Данные для авторизации в SASTAV SCA
SASTAV_SCA_URL = "http://192.168.13.62:8080"
AUTH_URL = f"{SASTAV_SCA_URL}/api/v1/auth/login"
AUTH_DATA = json.dumps({"login": "admin", "password": "1qazXSW@"}).encode()

# URL для отправки файлов на проверку в SASTAV SCA
SCAN_REPO_UUID = "ac130005-98a8-1568-8198-a894496b01f8"
SCAN_URL = f"{SASTAV_SCA_URL}/api/v1/repository/{SCAN_REPO_UUID}/scan"

# URL для проверки статуса сканирования в SASTAV SCA
SCAN_STATUS_URL_TEMPLATE = f"{SASTAV_SCA_URL}" + "/api/v1/artifact/{}/scan/info"

# URL для получения отчета о сканировании из SASTAV SCA
SCAN_REPORT_URL_TEMPLATE = f"{SASTAV_SCA_URL}" + "/api/v1/artifact/{}/metrics"

# URL для удаления ассетов из Nexus
DELETE_ASSET_URL_TEMPLATE = f"{NEXUS_URL}/service/rest/v1/assets/{{}}"

# Нежелательные расширения файлов
UNWANTED_EXTENSIONS = ['.md5', '.sha1', '.sha256', '.sha512']


# Получаем accessToken из SASTAV SCA
def get_access_token():
    try:
        req = urllib.request.Request(
            AUTH_URL,
            data=AUTH_DATA,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            auth_response = json.loads(response.read().decode())
            access_token = auth_response.get('accessToken')
            if access_token:
                print(f"Успешно получен токен доступа SASTAV SCA")
                return access_token
            else:
                print("Не удалось получить токен доступа из ответа SASTAV SCA")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"Ошибка HTTP при получении токена SASTAV SCA: {e.code} {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Ошибка подключения при получении токена SASTAV SCA: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка при получении токена SASTAV SCA: {str(e)}")
        sys.exit(1)


# Удаляем ассет из Nexus
def delete_asset_from_nexus(asset_id):
    try:
        delete_url = DELETE_ASSET_URL_TEMPLATE.format(asset_id)

        # Создаем заголовок для базовой аутентификации
        credentials = base64.b64encode(f"{NEXUS_USER}:{NEXUS_PASS}".encode()).decode()
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Basic {credentials}'
        }

        req = urllib.request.Request(
            url=delete_url,
            headers=headers,
            method='DELETE'
        )

        with urllib.request.urlopen(req) as response:
            if response.getcode() == 204:
                return True
            else:
                print(f"Не удалось удалить ассет {asset_id}. Код ответа: {response.getcode()}")
                return False

    except urllib.error.HTTPError as e:
        print(f"Ошибка HTTP при удалении ассета {asset_id}: {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"Ошибка подключения при удалении ассета {asset_id}: {e.reason}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при удалении ассета {asset_id}: {str(e)}")
        return False


# Отправляем файл на проверку в SASTAV SCA
def send_file_for_scanning(token, file_path, version="1.0"):
    try:
        # Подготавливаем multipart/form-data
        boundary = f"----WebKitFormBoundary{str(uuid.uuid4()).replace('-', '')}"

        # Читаем файл
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Создаем тело запроса
        body = []
        body.append(f"--{boundary}")
        body.append('Content-Disposition: form-data; name="version"')
        body.append('')
        body.append(version)

        body.append(f"--{boundary}")
        body.append(f'Content-Disposition: form-data; name="file"; filename="{file_path}"')
        body.append('Content-Type: application/octet-stream')
        body.append('')
        body = "\r\n".join(body).encode() + b"\r\n" + file_content + f"\r\n--{boundary}--\r\n".encode()

        # Создаем запрос
        req = urllib.request.Request(
            SCAN_URL,
            data=body,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            },
            method='POST'
        )

        # Отправляем запрос
        with urllib.request.urlopen(req) as response:
            scan_response = response.read().decode()
            print(f"Файл {file_path} отправлен на проверку в SASTAV SCA. Ответ: {scan_response}")
            return scan_response.strip('"')  # Убираем возможные кавычки вокруг UUID

    except Exception as e:
        print(f"Ошибка при отправке файла {file_path} на проверку в SASTAV SCA: {str(e)}")
        return None


# Проверяем статус сканирования в SASTAV SCA
def check_scan_status(token, scan_uuid):
    try:
        status_url = SCAN_STATUS_URL_TEMPLATE.format(scan_uuid)
        req = urllib.request.Request(
            status_url,
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
        )

        with urllib.request.urlopen(req) as response:
            status_data = json.loads(response.read().decode())
            return status_data.get('status')

    except Exception as e:
        print(f"Ошибка при проверке статуса сканирования {scan_uuid} в SASTAV SCA: {str(e)}")
        return None


# Получаем отчет о сканировании из SASTAV SCA
def get_scan_report(token, scan_uuid):
    try:
        report_url = SCAN_REPORT_URL_TEMPLATE.format(scan_uuid)
        req = urllib.request.Request(
            report_url,
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
        )

        with urllib.request.urlopen(req) as response:
            report_data = json.loads(response.read().decode())
            return report_data

    except Exception as e:
        print(f"Ошибка при получении отчета сканирования {scan_uuid} из SASTAV SCA: {str(e)}")
        return None


# Проверяем отчет на наличие блокирующих политик SCA
def check_sca_policies(report):
    if not report:
        print("Отчет отсутствует, проверка невозможна")
        return False

    # Ищем раздел с триажом (triage)
    for section in report:
        if section.get('type') == 'triage':
            # Ищем элемент с CRITICAL (блокирующие политики)
            for item in section.get('items', []):
                if item.get('name') == 'CRITICAL':
                    critical_count = item.get('value', 0)
                    print(f"Найдено блокирующих политик SCA: {critical_count}")

                    if critical_count > 0:
                        print("❌ Обнаружены блокирующие политики SCA!")
                        return False
                    else:
                        print("✅ Блокирующих политик SCA не обнаружено")
                        return True

    print("Раздел triage с CRITICAL не найден в отчете SASTAV SCA")
    return False


# Отслеживаем статус сканирования до завершения и получаем отчет
def wait_for_scan_completion_and_get_report(token, scan_uuid, max_attempts=30, delay_seconds=10):
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        status = check_scan_status(token, scan_uuid)

        if status is None:
            print(f"Не удалось получить статус для {scan_uuid} из SASTAV SCA")
            return None

        print(f"Статус сканирования {scan_uuid} в SASTAV SCA: {status} (попытка {attempt}/{max_attempts})")

        if status == "FINISHED":
            print(f"Сканирование {scan_uuid} в SASTAV SCA завершено!")
            # Получаем отчет после завершения сканирования
            report = get_scan_report(token, scan_uuid)
            if report:
                # print(f"Отчет по сканированию {scan_uuid} из SASTAV SCA:")
                # print(json.dumps(report, indent=2))

                # Проверяем наличие блокирующих политик SCA
                is_safe = check_sca_policies(report)
                return {"report": report, "is_safe": is_safe}
            else:
                print(f"Не удалось получить отчет для {scan_uuid} из SASTAV SCA")
                return None

        # Ждем перед следующей проверкой
        time.sleep(delay_seconds)

    print(f"Сканирование {scan_uuid} в SASTAV SCA не завершилось после {max_attempts} попыток")
    return None


# Получаем токен
access_token = get_access_token()

# Получаем текущее время и время 24 часа назад в UTC
current_time = datetime.datetime.utcnow()
past_time = current_time - datetime.timedelta(hours=24)


# Форматируем время в нужный формат для сравнения (ISO 8601)
def format_time(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")


current_time_str = format_time(current_time)
past_time_str = format_time(past_time)


# Проверяем, имеет ли URL нежелательное расширение
def has_unwanted_extension(url):
    if not url:
        return False
    return any(url.lower().endswith(ext) for ext in UNWANTED_EXTENSIONS)


# Создаем заголовок для базовой аутентификации
credentials = base64.b64encode(f"{NEXUS_USER}:{NEXUS_PASS}".encode()).decode()
headers = {
    'Accept': 'application/json',
    'Authorization': f'Basic {credentials}'
}

# Формируем запрос
req = urllib.request.Request(
    url=f"{API_URL}?group={REPO_COMPONENT_GROUP}&name={REPO_COMPONENT_NAME}",
    headers=headers
)

# Список для хранения результатов проверки
scan_results = []

try:
    # Выполняем запрос
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())

        # Обрабатываем элементы
        for item in data.get('items', []):
            for asset in item.get('assets', []):
                asset_id = asset.get('id')
                asset_time = asset.get('lastModified')
                download_url = asset.get('downloadUrl')

                if not all([asset_id, asset_time, download_url]):
                    continue

                # Пропускаем файлы с нежелательными расширениями
                if has_unwanted_extension(download_url):
                    continue

                try:
                    # Парсим время из ответа
                    asset_dt = datetime.datetime.strptime(
                        asset_time,
                        "%Y-%m-%dT%H:%M:%S.%f%z"
                    )
                    # Сравниваем время
                    if asset_dt.replace(tzinfo=None) >= past_time:
                        print(f"Артефакт {asset_id} был изменен за последние 24 часа:")
                        print(f"URL для скачивания: {download_url}")
                        print("---")

                        download_req = urllib.request.Request(url=download_url, headers=headers)
                        with urllib.request.urlopen(download_req) as resp:
                            filename = download_url.split('/')[-1]
                            with open(filename, 'wb') as f:
                                f.write(resp.read())
                            print(f"Скачан файл: {filename}")

                            # Отправляем файл на проверку в SASTAV SCA
                            scan_uuid = send_file_for_scanning(access_token, filename)
                            if scan_uuid:
                                print(f"Файл отправлен на проверку в SASTAV SCA, UUID: {scan_uuid}")

                                # Ожидаем завершения сканирования и получаем отчет
                                result = wait_for_scan_completion_and_get_report(access_token, scan_uuid)

                                # Сохраняем результат
                                if result:
                                    scan_results.append({
                                        "filename": filename,
                                        "asset_id": asset_id,
                                        "scan_uuid": scan_uuid,
                                        "is_safe": result["is_safe"],
                                        "report": result["report"]
                                    })

                                    # Если обнаружены блокирующие политики SCA, удаляем ассет из Nexus
                                    if not result["is_safe"]:
                                        print(f"❌ Файл {filename} содержит блокирующие политики SCA!")
                                        print(f"Пытаемся удалить ассет {asset_id} из Nexus...")

                                        # Удаляем ассет из Nexus
                                        if delete_asset_from_nexus(asset_id):
                                            print(f"Ассет {asset_id} успешно удален из Nexus")
                                        else:
                                            print(f"Не удалось удалить ассет {asset_id} из Nexus")

                except ValueError as e:
                    # Пропускаем артефакты с некорректным форматом времени
                    continue

        # Выводим итоговый отчет по всем проверенным файлам
        print("\n" + "=" * 50)
        print("ИТОГОВЫЙ ОТЧЕТ ПО ПРОВЕРКЕ SASTAV SCA")
        print("=" * 50)

        safe_files = [r for r in scan_results if r["is_safe"]]
        unsafe_files = [r for r in scan_results if not r["is_safe"]]

        print(f"Проверено файлов: {len(scan_results)}")
        print(f"Файлов без блокирующих политик SCA: {len(safe_files)}")
        print(f"Файлов с блокирующими политиками SCA: {len(unsafe_files)}")

        if unsafe_files:
            print("\nФайлы с блокирующими политиками SCA:")
            for result in unsafe_files:
                print(f"  - {result['filename']} (Asset ID: {result['asset_id']}, UUID: {result['scan_uuid']})")

            # Завершаем с ошибкой, если есть файлы с блокирующими политиками SCA
            sys.exit(1)
        else:
            print("\n✅ Все файлы прошли проверку SASTAV SCA!")

except urllib.error.HTTPError as e:
    if e.code == 401:
        print("Ошибка аутентификации: неверные учетные данные")
    else:
        print(f"Ошибка HTTP: {e.code} {e.reason}")
    sys.exit(1)
except urllib.error.URLError as e:
    print(f"Ошибка подключения: {e.reason}")
    sys.exit(1)
except Exception as e:
    print(f"Неожиданная ошибка: {str(e)}")
    sys.exit(1)