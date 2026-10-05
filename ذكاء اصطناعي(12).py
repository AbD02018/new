import requests
import json
import re
import uuid
import sys
from bs4 import BeautifulSoup

M = "https://ptero.pro"
A = f"{M}/wp-json/mlp/v1/chat-stream"

W = {
    "1": {"id": "ling-3.0-flash",           "name": "Ling 3.0 Flash"},
    "2": {"id": "deepseek-v4.1-flash:free", "name": "DeepSeek v4.1 Flash"},
    "3": {"id": "atria-dawn-preview",       "name": "Atria-Dawn-Preview"},
    "4": {"id": "agnes-2.5-flash",          "name": "Agnes 2.5 Flash"},
    "5": {"id": "agnes-3.0-flash",          "name": "Agnes 3.0 Flash"},
    "6": {"id": "laguna-s-2.1",             "name": "Laguna S 2.1"},
}

P = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def fetch_real_session():
    session = requests.Session()
    headers = {
        'User-Agent': P,
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        'Accept-Language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        'Accept-Encoding': "gzip, deflate, br",
        'Connection': "keep-alive",
        'Upgrade-Insecure-Requests': "1",
    }

    try:
        response = session.get(M, headers=headers, timeout=30)
        if response.status_code != 200:
            return None

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        nonce = None
        patterns = [
            r'["\']nonce["\']\s*:\s*["\']([a-f0-9]+)["\']',
            r'mlp_nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
            r'wp_nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
            r'x-wp-nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
            r'data-nonce=["\']([a-f0-9]+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                nonce = match.group(1)
                break

        if not nonce:
            for script in soup.find_all('script'):
                if script.string and 'nonce' in script.string:
                    match = re.search(r'["\']([a-f0-9]{10})["\']', script.string)
                    if match:
                        nonce = match.group(1)
                        break

        if not nonce:
            return None

        guest_token = None
        for cookie in session.cookies:
            if any(k in cookie.name.lower() for k in ['mlp', 'guest', 'token']):
                guest_token = cookie.value
                break

        if not guest_token:
            match = re.search(r'guest[_-]?token["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']', html, re.IGNORECASE)
            guest_token = match.group(1) if match else uuid.uuid4().hex

        return {
            "session": session,
            "nonce": nonce,
            "guest_token": guest_token,
            "conversation_id": str(uuid.uuid4()),
        }
    except Exception:
        return None


def chat_with_model(model_id, user_message, session_data, model_display_name):
    payload = {
        "message": user_message,
        "model": model_id,
        "conversation_id": session_data["conversation_id"],
        "attachments": [],
        "history": [],
        "lang": "ar",
        "github_repo": "",
        "mode": "quick"
    }

    headers = {
        'User-Agent': P,
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        'sec-ch-ua-mobile': "?1",
        'x-wp-nonce': session_data["nonce"],
        'x-mlp-guest-token': session_data["guest_token"],
        'x-mlp-guest-username': f"user_{session_data['conversation_id'][:6]}",
        'origin': M,
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"{M}/",
        'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        'priority': "u=1, i",
    }

    try:
        response = session_data["session"].post(
            A, json=payload, headers=headers, stream=True, timeout=60
        )

        if response.status_code != 200:
            return None, None

        full_reply = ""

        print()
        print(f"{model_display_name}:")

        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "keepalive":
                continue
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if "token" in data:
                full_reply += data["token"]
                print(data["token"], end="", flush=True)
            elif data.get("done"):
                print()
                if data.get("conversation_id"):
                    session_data["conversation_id"] = data["conversation_id"]
                return full_reply, data

        return full_reply, None

    except requests.exceptions.RequestException:
        return None, None


def select_model():
    print("النماذج المتاحة:")
    for key, info in W.items():
        print(f"  [{key}] {info['name']}")
    while True:
        choice = input("\nاختر رقم النموذج: ").strip()
        if choice in W:
            return W[choice]
        print("اختيار غير صحيح.")


def main():
    session_data = fetch_real_session()
    if not session_data:
        sys.exit(1)

    model_info = select_model()

    while True:
        try:
            print()
            user_msg = input("أنت: ").strip()

            if not user_msg:
                continue

            if user_msg.lower() in ['exit', 'خروج', 'quit']:
                break

            reply, meta = chat_with_model(
                model_info["id"], user_msg, session_data, model_info["name"]
            )

            if not reply:
                session_data = fetch_real_session()
                if not session_data:
                    break
                reply, meta = chat_with_model(
                    model_info["id"], user_msg, session_data, model_info["name"]
                )

        except KeyboardInterrupt:
            break
        except Exception:
            pass


if __name__ == "__main__":
    main()