import json
import ssl
import urllib.request

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}
CTX = ssl.create_default_context()


def try_url(name: str, url: str, *, json_body: bool = False) -> None:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            data = r.read()
        if json_body:
            j = json.loads(data)
            if isinstance(j, dict):
                if "items" in j:
                    print(name, "OK", "items", len(j["items"]))
                elif "jobs" in j:
                    print(name, "OK", "jobs", len(j["jobs"]))
                else:
                    print(name, "OK", "keys", list(j.keys())[:6])
            elif isinstance(j, list):
                print(name, "OK", "list", len(j))
        else:
            print(name, "OK", "bytes", len(data))
    except Exception as e:
        print(name, "FAIL", type(e).__name__, str(e)[:80])


try_url("hh_api", "https://api.hh.ru/vacancies?text=python&per_page=3", json_body=True)
try_url("zarplata_api", "https://api.zarplata.ru/vacancies?text=python&per_page=3", json_body=True)
try_url("superjob", "https://www.superjob.ru/vakansii/programmist-python.html")
try_url("rabota_ru", "https://www.rabota.ru/vacancy?query=python")
try_url("trudvsem", "https://trudvsem.ru/vacancy/search?text=python")
try_url("jobicy", "https://jobicy.com/api/v2/remote-jobs?count=5&tag=python", json_body=True)
try_url("arbeitnow", "https://www.arbeitnow.com/api/job-board-api", json_body=True)
try_url("findwork", "https://findwork.dev/api/jobs/?search=python", json_body=True)
try_url("himalayas", "https://himalayas.app/jobs/api?limit=5", json_body=True)
