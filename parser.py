from bs4 import BeautifulSoup
import httpx
from concurrent.futures import ThreadPoolExecutor
import threading


try:
    with open("profiles.txt", "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("❌ Файл profiles.txt не найден.")
    links = []


try:
    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("⚠️ Файл proxies.txt не найден.")
    proxies = []


if len(proxies) < len(links):
    print("⚠️ Прокси меньше, чем ссылок. Некоторые запросы будут без прокси.")


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0.0.0 Safari/537.36'
}


lock = threading.Lock()


def process_url(args):
    url, proxy = args
    mounts = {}

    if proxy:
        if not proxy.startswith("http://"):
            proxy_url = f"http://{proxy}"
        else:
            proxy_url = proxy

        transport = httpx.HTTPTransport(proxy=proxy_url, verify=False)
        mounts = {
            "http://": transport,
            "https://": transport,
        }

    try:
        with httpx.Client(headers=headers, mounts=mounts, timeout=15) as client:
            response = client.get(url)

            if response.status_code != 200:
                print(f"❌ Ошибка {response.status_code} при загрузке {url}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all("div", {"class": "iva-item-root-Kcj9I"})

            if not items:
                print(f"⚠️ На странице {url} не найдено товаров.")
                return

            result = [f"Ссылка: {url}\n"]

            for item in items:
                try:
                    name_tag = item.find("div", class_="iva-item-title-mxG7F")
                    price_tag = item.find("span", class_="styles-module-size_xm-RKzt0")

                    name = name_tag.text.strip() if name_tag else "Название не найдено"
                    price = price_tag.text.strip() if price_tag else "Цена не найдена"

                    print(f"[✓] {name} — {price}")
                    result.append(f"Название: {name}\nЦена: {price}\n{'-'*40}\n")
                except Exception as e:
                    print("⚠️ Ошибка при парсинге элемента:", e)
                    continue

            result.append("="*80 + "\n\n")

            with lock:
                with open("results.txt", "a", encoding="utf-8") as out:
                    out.writelines(result)

    except Exception as e:
        print(f"❌ Ошибка при обработке {url} с прокси {proxy}: {e}")


if __name__ == "__main__":
    if not links:
        print("Нет ссылок для обработки. Выход.")
        exit()

    tasks = [(links[i], proxies[i] if i < len(proxies) else None) for i in range(len(links))]

    print(f"🚀 Начинаем парсинг {len(links)} профилей...")

    with ThreadPoolExecutor(max_workers=min(10, len(links))) as executor:
        executor.map(process_url, tasks)

    print("✅ Завершено. Результаты в файле results.txt.")
