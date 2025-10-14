import time
from MonitoringSystem import run_user_check
from DomainManagementEngine import DomainManagementEngine as DME

def ensure_domains(username: str, domains: list[str]):
    """Заполняем пользователю домены, если пусто/нужно."""
    dme = DME()
    current = {d["domain"] for d in dme.list_domains(username)}
    for raw in domains:
        ok, host, _ = dme.validate_domain(raw)  # валидация/нормализация внутри DME
        if ok and host not in current:
            dme.add_domain_trusted(username, host)  # без повторной валидации
            current.add(host)

def time_scan(username: str) -> float:
    """Запуск скана с измерением времени."""
    t0 = time.perf_counter()
    result = run_user_check(username)   # внутренняя функция уже обновляет JSON
    # можно также взять result.get("duration"), если вы её возвращаете из run_user_check
    dt = time.perf_counter() - t0
    print(f"{username}'s domains check ended in {dt:.2f} Seconds.")
    return dt

if __name__ == "__main__":
    # Тестовые «пользователи» и домены для каждого
    tests = {
        "test1": ["google.com", "github.com", "wikipedia.org", "netflix.com"],
        "test2": ["example.com", "openai.com", "microsoft.com", "apple.com"],
        "test3": ["craigslist.org", "duckduckgo.com", "cloudflare.com", "python.org"],
        "test4": ["bbc.co.uk", "paypal.com", "paypal.com", "harvard.edu", "linkedin.com"],
        "test5": ["github.com", "apple.com", "twitch.tv", "duckduckgo.com", "notion.so"],

    }

    # 1) подготовка доменов
    for user, doms in tests.items():
        ensure_domains(user, doms)

    # 2) последовательное измерение
    for user in tests.keys():
        time_scan(user)
