
"""
SCTG Captcha Solver API Client
==============================
Python client for solving various types of CAPTCHAs using SCTG.xyz service.

Supported CAPTCHA types:
- Normal/Image CAPTCHA (text on image)
- reCAPTCHA v2/v3
- Cloudflare Turnstile
- GeeTest
- FunCaptcha (Arkose Labs)
- Yandex Smart Captcha
- Text CAPTCHA
- And more...

API Endpoints:
- Submit: https://api.sctg.xyz/in.php
- Result: https://api.sctg.xyz/res.php
"""

import requests
import time
import base64
from typing import Optional, Dict, Any, Union
from enum import Enum


class CaptchaType(Enum):
    """Supported CAPTCHA types"""
    NORMAL = "post"           # Image CAPTCHA with text
    TEXT = "text"             # Text-based CAPTCHA
    RECAPTCHA_V2 = "userrecaptcha"
    RECAPTCHA_V3 = "userrecaptcha"
    TURNSTILE = "turnstile"
    GEETEST = "geetest"
    FUNCAPTCHA = "funcaptcha"
    YANDEX_SMART = "yandex"
    ANTIBOT = "antibot"
    RSCAPTCHA = "rscaptcha"
    BASILISK = "basilisk"
    PUZZLE = "puzzle"
    KEYCAPTCHA = "keycaptcha"
    COORDINATES = "coordinates"
    GRID = "grid"
    ROTATE = "rotatecaptcha"
    CANVAS = "canvas"
    AUDIO = "audio"


class SCTGCaptchaSolver:
    """
    SCTG.xyz CAPTCHA Solving API Client

    Usage:
        solver = SCTGCaptchaSolver(api_key="your_api_key")

        # Solve image CAPTCHA
        result = solver.solve_image("path/to/captcha.jpg")

        # Solve reCAPTCHA v2
        result = solver.solve_recaptcha_v2(
            sitekey="6Le-wvkS...",
            pageurl="https://example.com"
        )
    """

    # API Endpoints
    SUBMIT_URL = "https://api.sctg.xyz/in.php"
    RESULT_URL = "https://api.sctg.xyz/res.php"

    # Alternative servers (for redundancy)
    SERVERS = [
        "https://api.sctg.xyz",
        "https://sctg.xyz",
        "https://ru.sctg.xyz"
    ]

    # Default timeouts
    DEFAULT_TIMEOUT = 120      # seconds for normal CAPTCHA
    RECAPTCHA_TIMEOUT = 600    # seconds for reCAPTCHA
    POLLING_INTERVAL = 5       # seconds between polls

    def __init__(
        self,
        api_key: str,
        default_timeout: int = 120,
        recaptcha_timeout: int = 600,
        polling_interval: int = 5,
        use_json: bool = True
    ):
        """
        Initialize the CAPTCHA solver.

        Args:
            api_key: Your SCTG API key
            default_timeout: Timeout for normal CAPTCHAs (seconds)
            recaptcha_timeout: Timeout for reCAPTCHA (seconds)
            polling_interval: Interval between result polls (seconds)
            use_json: Use JSON format for responses
        """
        self.api_key = api_key
        self.default_timeout = default_timeout
        self.recaptcha_timeout = recaptcha_timeout
        self.polling_interval = max(polling_interval, 5)  # Min 5 seconds
        self.use_json = 1 if use_json else 0
        self.session = requests.Session()

    def _submit_captcha(self, payload: Dict[str, Any]) -> str:
        """
        Submit CAPTCHA to the API.

        Args:
            payload: Dictionary containing CAPTCHA data

        Returns:
            CAPTCHA ID if successful

        Raises:
            Exception: If submission fails
        """
        # Add API key and JSON preference
        payload["key"] = self.api_key
        payload["json"] = self.use_json

        try:
            response = self.session.post(
                self.SUBMIT_URL,
                data=payload,
                timeout=30
            )
            response.raise_for_status()

            if self.use_json:
                data = response.json()
                if data.get("status") == 1:
                    return data["request"]
                else:
                    raise Exception(f"API Error: {data.get('request', 'Unknown error')}")
            else:
                result = response.text
                if result.startswith("OK|"):
                    return result.split("|")[1]
                else:
                    raise Exception(f"API Error: {result}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    def _get_result(self, captcha_id: str, timeout: int) -> str:
        """
        Poll for CAPTCHA result.

        Args:
            captcha_id: The CAPTCHA task ID
            timeout: Maximum time to wait (seconds)

        Returns:
            CAPTCHA solution text/token

        Raises:
            Exception: If polling fails or times out
        """
        params = {
            "key": self.api_key,
            "action": "get",
            "id": captcha_id,
            "json": self.use_json
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    self.RESULT_URL,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                if self.use_json:
                    data = response.json()
                    if data.get("status") == 1:
                        return data["request"]
                    elif data.get("request") == "CAPCHA_NOT_READY":
                        time.sleep(self.polling_interval)
                        continue
                    else:
                        raise Exception(f"API Error: {data.get('request')}")
                else:
                    result = response.text
                    if result.startswith("OK|"):
                        return result.split("|")[1]
                    elif result == "CAPCHA_NOT_READY":
                        time.sleep(self.polling_interval)
                        continue
                    else:
                        raise Exception(f"API Error: {result}")

            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error during polling: {str(e)}")

        raise Exception(f"Timeout: CAPTCHA not solved within {timeout} seconds")

    def solve_image(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        numeric: int = 0,
        min_length: int = 0,
        max_length: int = 0,
        phrase: int = 0,
        case_sensitive: int = 0,
        calc: int = 0,
        language: Optional[str] = None,
        hint_text: Optional[str] = None,
        hint_image: Optional[str] = None
    ) -> str:
        """
        Solve an image CAPTCHA (text on image).

        Args:
            image_path: Path to local image file
            image_base64: Base64 encoded image string
            image_url: URL of the image
            numeric: 0=any, 1=only numbers, 2=only letters
            min_length: Minimum answer length
            max_length: Maximum answer length
            phrase: 0=single word, 1=multiple words
            case_sensitive: 0=no, 1=yes
            calc: 0=no calculation, 1=requires calculation
            language: Language code (e.g., 'en', 'ru')
            hint_text: Hint text for workers
            hint_image: Hint image path

        Returns:
            Solved CAPTCHA text
        """
        payload = {
            "method": "post",
            "numeric": numeric,
            "min_len": min_length,
            "max_len": max_length,
            "phrase": phrase,
            "case": case_sensitive,
            "calc": calc
        }

        if language:
            payload["lang"] = language
        if hint_text:
            payload["textinstructions"] = hint_text

        # Handle image input
        if image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
            payload["body"] = base64.b64encode(image_data).decode("utf-8")
        elif image_base64:
            payload["body"] = image_base64
        elif image_url:
            payload["body"] = image_url
        else:
            raise ValueError("Must provide image_path, image_base64, or image_url")

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def solve_text(self, text: str) -> str:
        """
        Solve a text-based CAPTCHA.

        Args:
            text: The CAPTCHA question/text

        Returns:
            Answer text
        """
        payload = {
            "method": "text",
            "text": text
        }

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def solve_recaptcha_v2(
        self,
        sitekey: str,
        pageurl: str,
        invisible: bool = False,
        enterprise: bool = False,
        datas: Optional[str] = None,
        cookies: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> str:
        """
        Solve Google reCAPTCHA v2.

        Args:
            sitekey: The reCAPTCHA site key
            pageurl: URL of the page with reCAPTCHA
            invisible: Whether it's invisible reCAPTCHA
            enterprise: Whether it's reCAPTCHA Enterprise
            datas: data-s parameter (for Enterprise)
            cookies: Cookies for solving
            user_agent: User-Agent string
            proxy: Proxy in format login:pass@ip:port
            proxy_type: Proxy type (HTTP, HTTPS, SOCKS4, SOCKS5)

        Returns:
            reCAPTCHA response token
        """
        payload = {
            "method": "userrecaptcha",
            "googlekey": sitekey,
            "pageurl": pageurl,
            "invisible": 1 if invisible else 0,
            "enterprise": 1 if enterprise else 0,
            "version": "v2"
        }

        if datas:
            payload["data-s"] = datas
        if cookies:
            payload["cookies"] = cookies
        if user_agent:
            payload["userAgent"] = user_agent
        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.recaptcha_timeout)

    def solve_recaptcha_v3(
        self,
        sitekey: str,
        pageurl: str,
        action: str = "verify",
        min_score: float = 0.3,
        enterprise: bool = False,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> str:
        """
        Solve Google reCAPTCHA v3.

        Args:
            sitekey: The reCAPTCHA site key
            pageurl: URL of the page with reCAPTCHA
            action: Action name (e.g., 'verify', 'login')
            min_score: Minimum score required
            enterprise: Whether it's reCAPTCHA Enterprise
            proxy: Proxy string
            proxy_type: Proxy type

        Returns:
            reCAPTCHA response token
        """
        payload = {
            "method": "userrecaptcha",
            "googlekey": sitekey,
            "pageurl": pageurl,
            "version": "v3",
            "action": action,
            "min_score": min_score,
            "enterprise": 1 if enterprise else 0
        }

        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.recaptcha_timeout)

    def solve_turnstile(
        self,
        sitekey: str,
        pageurl: str,
        action: Optional[str] = None,
        data: Optional[str] = None,
        pagedata: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> str:
        """
        Solve Cloudflare Turnstile CAPTCHA.

        Args:
            sitekey: The Turnstile site key
            pageurl: URL of the page
            action: Action parameter
            data: cData parameter
            pagedata: chlPageData parameter
            user_agent: User-Agent string
            proxy: Proxy string
            proxy_type: Proxy type

        Returns:
            Turnstile response token
        """
        payload = {
            "method": "turnstile",
            "sitekey": sitekey,
            "pageurl": pageurl
        }

        if action:
            payload["action"] = action
        if data:
            payload["data"] = data
        if pagedata:
            payload["pagedata"] = pagedata
        if user_agent:
            payload["userAgent"] = user_agent
        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.recaptcha_timeout)

    def solve_geetest(
        self,
        gt: str,
        challenge: str,
        pageurl: str,
        api_server: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Solve GeeTest CAPTCHA.

        Args:
            gt: GeeTest gt parameter
            challenge: GeeTest challenge parameter
            pageurl: URL of the page
            api_server: GeeTest API server
            proxy: Proxy string
            proxy_type: Proxy type

        Returns:
            Dictionary with challenge, validate, and seccode
        """
        payload = {
            "method": "geetest",
            "gt": gt,
            "challenge": challenge,
            "pageurl": pageurl
        }

        if api_server:
            payload["api_server"] = api_server
        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        result = self._get_result(captcha_id, self.default_timeout)

        # Parse JSON result
        import json
        try:
            return json.loads(result)
        except:
            return {"result": result}

    def solve_geetest_v4(
        self,
        captcha_id: str,
        pageurl: str,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Solve GeeTest v4 CAPTCHA.

        Args:
            captcha_id: GeeTest captcha_id parameter
            pageurl: URL of the page
            proxy: Proxy string
            proxy_type: Proxy type

        Returns:
            Dictionary with solution tokens
        """
        payload = {
            "method": "geetest_v4",
            "captcha_id": captcha_id,
            "pageurl": pageurl
        }

        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        result = self._get_result(captcha_id, self.default_timeout)

        import json
        try:
            return json.loads(result)
        except:
            return {"result": result}

    def solve_funcaptcha(
        self,
        sitekey: str,
        pageurl: str,
        data: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> str:
        """
        Solve FunCaptcha (Arkose Labs).

        Args:
            sitekey: FunCaptcha public key
            pageurl: URL of the page
            data: Additional data parameter
            user_agent: User-Agent string
            proxy: Proxy string
            proxy_type: Proxy type

        Returns:
            FunCaptcha token
        """
        payload = {
            "method": "funcaptcha",
            "publickey": sitekey,
            "pageurl": pageurl
        }

        if data:
            payload["data[blob]"] = data
        if user_agent:
            payload["userAgent"] = user_agent
        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.recaptcha_timeout)

    def solve_yandex_smart(
        self,
        sitekey: str,
        pageurl: str,
        proxy: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> str:
        """
        Solve Yandex Smart Captcha.

        Args:
            sitekey: Yandex site key
            pageurl: URL of the page
            proxy: Proxy string
            proxy_type: Proxy type

        Returns:
            Yandex Smart Captcha token
        """
        payload = {
            "method": "yandex",
            "sitekey": sitekey,
            "pageurl": pageurl
        }

        if proxy:
            payload["proxy"] = proxy
            payload["proxytype"] = proxy_type or "SOCKS5"

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def solve_coordinates(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        textinstructions: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Solve a CAPTCHA that requires clicking on coordinates.

        Args:
            image_path: Path to image file
            image_base64: Base64 encoded image
            textinstructions: Instructions for workers
            language: Language code

        Returns:
            Coordinates string (e.g., "coordinate:x=39,y=59;x=252,y=72")
        """
        payload = {
            "method": "coordinates",
            "coordinatescaptcha": 1
        }

        if textinstructions:
            payload["textinstructions"] = textinstructions
        if language:
            payload["lang"] = language

        if image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
            payload["body"] = base64.b64encode(image_data).decode("utf-8")
        elif image_base64:
            payload["body"] = image_base64
        else:
            raise ValueError("Must provide image_path or image_base64")

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def solve_grid(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        recaptcharows: int = 3,
        recaptchacols: int = 3,
        textinstructions: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Solve grid-based CAPTCHA (like old reCAPTCHA v2).

        Args:
            image_path: Path to image file
            image_base64: Base64 encoded image
            recaptcharows: Number of rows in grid
            recaptchacols: Number of columns in grid
            textinstructions: Instructions
            language: Language code

        Returns:
            Grid cell numbers (e.g., "click:3/8/9")
        """
        payload = {
            "method": "post",
            "recaptcha": 1,
            "recaptcharows": recaptcharows,
            "recaptchacols": recaptchacols
        }

        if textinstructions:
            payload["textinstructions"] = textinstructions
        if language:
            payload["lang"] = language

        if image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
            payload["body"] = base64.b64encode(image_data).decode("utf-8")
        elif image_base64:
            payload["body"] = image_base64
        else:
            raise ValueError("Must provide image_path or image_base64")

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def solve_rotate(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        angle: int = 40,
        language: Optional[str] = None
    ) -> str:
        """
        Solve rotate CAPTCHA (FunCaptcha style).

        Args:
            image_path: Path to image file
            image_base64: Base64 encoded image
            angle: Rotation angle per step (default 40)
            language: Language code

        Returns:
            Rotation angles (e.g., "40|200|-120")
        """
        payload = {
            "method": "rotatecaptcha",
            "angle": angle
        }

        if language:
            payload["lang"] = language

        if image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
            payload["body"] = base64.b64encode(image_data).decode("utf-8")
        elif image_base64:
            payload["body"] = image_base64
        else:
            raise ValueError("Must provide image_path or image_base64")

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def solve_audio(
        self,
        audio_path: Optional[str] = None,
        audio_base64: Optional[str] = None,
        language: str = "en"
    ) -> str:
        """
        Solve audio CAPTCHA (speech to text).

        Args:
            audio_path: Path to audio file (mp3)
            audio_base64: Base64 encoded audio
            language: Audio language (en, fr, de, el, pt, ru)

        Returns:
            Transcribed text
        """
        payload = {
            "method": "audio",
            "lang": language
        }

        if audio_path:
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            payload["body"] = base64.b64encode(audio_data).decode("utf-8")
        elif audio_base64:
            payload["body"] = audio_base64
        else:
            raise ValueError("Must provide audio_path or audio_base64")

        captcha_id = self._submit_captcha(payload)
        return self._get_result(captcha_id, self.default_timeout)

    def get_balance(self) -> float:
        """
        Get account balance.

        Returns:
            Account balance as float
        """
        payload = {
            "key": self.api_key,
            "action": "getbalance",
            "json": self.use_json
        }

        try:
            response = self.session.get(self.RESULT_URL, params=payload, timeout=30)
            response.raise_for_status()

            if self.use_json:
                data = response.json()
                if data.get("status") == 1:
                    return float(data["request"])
                else:
                    raise Exception(f"API Error: {data.get('request')}")
            else:
                return float(response.text)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    def report_correct(self, captcha_id: str) -> bool:
        """
        Report a correctly solved CAPTCHA.

        Args:
            captcha_id: The CAPTCHA ID

        Returns:
            True if report was successful
        """
        return self._report(captcha_id, True)

    def report_incorrect(self, captcha_id: str) -> bool:
        """
        Report an incorrectly solved CAPTCHA.

        Args:
            captcha_id: The CAPTCHA ID

        Returns:
            True if report was successful
        """
        return self._report(captcha_id, False)

    def _report(self, captcha_id: str, is_correct: bool) -> bool:
        """Internal report method"""
        action = "reportgood" if is_correct else "reportbad"

        payload = {
            "key": self.api_key,
            "action": action,
            "id": captcha_id,
            "json": self.use_json
        }

        try:
            response = self.session.get(self.RESULT_URL, params=payload, timeout=30)
            response.raise_for_status()

            if self.use_json:
                data = response.json()
                return data.get("status") == 1
            else:
                return response.text == "OK_REPORT_RECORDED"

        except requests.exceptions.RequestException:
            return False


# ============================================================================
# FLASK API EXAMPLE
# ============================================================================
"""
To run the Flask API:
    pip install flask
    python sctg_api.py

Then send requests to:
    http://localhost:5000/solve/image
    http://localhost:5000/solve/recaptcha_v2
    etc.
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize solver with your API key
# Replace with your actual API key
SOLVER = SCTGCaptchaSolver(api_key="Uosbi2t23tLFF7D1ro9yyX1EOJ61ER8I")


@app.route("/")
def index():
    """API Home"""
    return jsonify({
        "service": "SCTG Captcha Solver API",
        "version": "1.0",
        "endpoints": [
            "/solve/image",
            "/solve/text",
            "/solve/recaptcha_v2",
            "/solve/recaptcha_v3",
            "/solve/turnstile",
            "/solve/geetest",
            "/solve/funcaptcha",
            "/solve/yandex",
            "/balance"
        ]
    })


@app.route("/solve/image", methods=["POST"])
def solve_image_endpoint():
    """
    Solve Image CAPTCHA

    Request Body (JSON):
    {
        "image_base64": "base64_string",  // OR
        "image_url": "http://...",        // OR
        "image_path": "/path/to/file",
        "numeric": 0,
        "min_length": 0,
        "max_length": 0,
        "language": "en"
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_image(
            image_path=data.get("image_path"),
            image_base64=data.get("image_base64"),
            image_url=data.get("image_url"),
            numeric=data.get("numeric", 0),
            min_length=data.get("min_length", 0),
            max_length=data.get("max_length", 0),
            language=data.get("language")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/text", methods=["POST"])
def solve_text_endpoint():
    """
    Solve Text CAPTCHA

    Request Body (JSON):
    {
        "text": "What is 2+2?"
    }
    """
    try:
        data = request.get_json()
        text = data.get("text")

        if not text:
            return jsonify({"success": False, "error": "Missing 'text' field"}), 400

        result = SOLVER.solve_text(text)

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/recaptcha_v2", methods=["POST"])
def solve_recaptcha_v2_endpoint():
    """
    Solve reCAPTCHA v2

    Request Body (JSON):
    {
        "sitekey": "6Le-wvkS...",
        "pageurl": "https://example.com",
        "invisible": false,
        "enterprise": false,
        "proxy": "login:pass@ip:port",
        "proxy_type": "SOCKS5"
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_recaptcha_v2(
            sitekey=data["sitekey"],
            pageurl=data["pageurl"],
            invisible=data.get("invisible", False),
            enterprise=data.get("enterprise", False),
            proxy=data.get("proxy"),
            proxy_type=data.get("proxy_type")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/recaptcha_v3", methods=["POST"])
def solve_recaptcha_v3_endpoint():
    """
    Solve reCAPTCHA v3

    Request Body (JSON):
    {
        "sitekey": "6Le-wvkS...",
        "pageurl": "https://example.com",
        "action": "verify",
        "min_score": 0.3
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_recaptcha_v3(
            sitekey=data["sitekey"],
            pageurl=data["pageurl"],
            action=data.get("action", "verify"),
            min_score=data.get("min_score", 0.3),
            proxy=data.get("proxy"),
            proxy_type=data.get("proxy_type")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/turnstile", methods=["POST"])
def solve_turnstile_endpoint():
    """
    Solve Cloudflare Turnstile

    Request Body (JSON):
    {
        "sitekey": "0x1AAAAAAAA...",
        "pageurl": "https://example.com",
        "action": "managed",
        "data": "...",
        "pagedata": "..."
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_turnstile(
            sitekey=data["sitekey"],
            pageurl=data["pageurl"],
            action=data.get("action"),
            data=data.get("data"),
            pagedata=data.get("pagedata"),
            proxy=data.get("proxy"),
            proxy_type=data.get("proxy_type")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/geetest", methods=["POST"])
def solve_geetest_endpoint():
    """
    Solve GeeTest CAPTCHA

    Request Body (JSON):
    {
        "gt": "f1ab2cdefa...",
        "challenge": "12345678abc...",
        "pageurl": "https://example.com"
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_geetest(
            gt=data["gt"],
            challenge=data["challenge"],
            pageurl=data["pageurl"],
            proxy=data.get("proxy"),
            proxy_type=data.get("proxy_type")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/funcaptcha", methods=["POST"])
def solve_funcaptcha_endpoint():
    """
    Solve FunCaptcha

    Request Body (JSON):
    {
        "sitekey": "public_key...",
        "pageurl": "https://example.com",
        "data": "optional_blob"
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_funcaptcha(
            sitekey=data["sitekey"],
            pageurl=data["pageurl"],
            data=data.get("data"),
            proxy=data.get("proxy"),
            proxy_type=data.get("proxy_type")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/solve/yandex", methods=["POST"])
def solve_yandex_endpoint():
    """
    Solve Yandex Smart Captcha

    Request Body (JSON):
    {
        "sitekey": "yandex_key...",
        "pageurl": "https://example.com"
    }
    """
    try:
        data = request.get_json()

        result = SOLVER.solve_yandex_smart(
            sitekey=data["sitekey"],
            pageurl=data["pageurl"],
            proxy=data.get("proxy"),
            proxy_type=data.get("proxy_type")
        )

        return jsonify({
            "success": True,
            "solution": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/balance", methods=["GET"])
def get_balance_endpoint():
    """Get account balance"""
    try:
        balance = SOLVER.get_balance()
        return jsonify({
            "success": True,
            "balance": balance
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/report", methods=["POST"])
def report_endpoint():
    """
    Report CAPTCHA result

    Request Body (JSON):
    {
        "captcha_id": "12345",
        "correct": true  // or false
    }
    """
    try:
        data = request.get_json()
        captcha_id = data.get("captcha_id")
        correct = data.get("correct", True)

        if correct:
            result = SOLVER.report_correct(captcha_id)
        else:
            result = SOLVER.report_incorrect(captcha_id)

        return jsonify({
            "success": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Run Flask API server
    print("=" * 60)
    print("SCTG Captcha Solver API Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  POST /solve/image       - Solve image CAPTCHA")
    print("  POST /solve/text        - Solve text CAPTCHA")
    print("  POST /solve/recaptcha_v2 - Solve reCAPTCHA v2")
    print("  POST /solve/recaptcha_v3 - Solve reCAPTCHA v3")
    print("  POST /solve/turnstile   - Solve Cloudflare Turnstile")
    print("  POST /solve/geetest     - Solve GeeTest")
    print("  POST /solve/funcaptcha  - Solve FunCaptcha")
    print("  POST /solve/yandex      - Solve Yandex Smart Captcha")
    print("  GET  /balance           - Get account balance")
    print("  POST /report            - Report CAPTCHA result")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
