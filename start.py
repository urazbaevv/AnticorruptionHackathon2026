"""
Anticorruption AI Agent System — Server
Hech narsa o'rnatish shart emas! Faqat shu faylni ikki marta bosing.
Python standart kutubxonasi bilan ishlaydi.
"""

import http.server
import json
import os
import webbrowser
import urllib.request
import urllib.error
import uuid
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = 3000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

os.makedirs(DATA_DIR, exist_ok=True)

# =========== AGENT PROMPTS ===========
AGENT_PROMPTS = {
    "LAW_SCANNER": """Siz O'zbekiston Respublikasining qonun hujjatlarini tahlil qiluvchi AGENT-1: LAW_SCANNER (Qonun Bo'shliqlarini Topuvchi) siz.
Rol: Yangi chiqayotgan qonun hujjatni satr-satr tahlil qilasiz.
Vazifalar:
  - Qonunni aylanib o'tish mumkin bo'lgan zaif nuqtalarni aniqlash
  - Noaniq, ikki ma'noli yozilgan moddalarni belgilash
  - Diskresion vakolatlarning kengligini aniqlash
  - "Mansabdor shaxs qarorida", "muvofiqlashtirilgan holda" iboralarni flaglash
  - XAVF_DARAJASI: [KRITIK | YUQORI | O'RTA | PAST]

Faqat JSON formatda javob bering, hech qanday qo'shimcha izohlarsiz:
{
  "agent": "LAW_SCANNER",
  "document_id": "doc_1",
  "scan_timestamp": "2026-04-25T15:00:00Z",
  "vulnerabilities": [
    {
      "article": "Modda N",
      "clause": "Qism N",
      "original_text": "...",
      "vulnerability_type": "...",
      "risk_level": "KRITIK",
      "corruption_scenario": "...",
      "bypass_methods": ["...", "..."],
      "confidence_score": 0.95
    }
  ],
  "total_vulnerabilities": 1,
  "critical_count": 1,
  "summary": "..."
}""",
    "CONFLICT_DETECTOR": """Siz AGENT-3: CONFLICT_DETECTOR (Qarama-qarshilik Topuvchi) siz.
Rol: Yangi qonun hujjat bilan amaldagi qonunlar o'rtasidagi ziddiyatlarni aniqlaysiz.

Faqat JSON formatda javob bering:
{
  "agent": "CONFLICT_DETECTOR",
  "new_law": "...",
  "analysis_date": "...",
  "conflicts": [
    {
      "conflict_id": "C1",
      "new_law_article": "...",
      "new_law_text": "...",
      "existing_law_code": "...",
      "existing_law_article": "...",
      "existing_law_text": "...",
      "conflict_type": "...",
      "conflict_description": "...",
      "legal_gap": "...",
      "severity": "...",
      "citizen_impact": "..."
    }
  ],
  "regulatory_gaps": ["...", "..."],
  "supersession_analysis": "..."
}""",
    "SOLUTION_ARCHITECT": """Siz AGENT-2: SOLUTION_ARCHITECT (Yechim Yaratuvchi) siz.
Rol: AGENT-1 topgan har bir bo'shliq uchun aniq yechim berasiz.

Faqat JSON formatda javob bering:
{
  "agent": "SOLUTION_ARCHITECT",
  "linked_vulnerability_id": "...",
  "solutions": [
    {
      "article": "...",
      "original_text": "...",
      "corrected_text": "...",
      "changes_summary": "...",
      "rationale": "...",
      "international_standard": "...",
      "implementation_difficulty": "...",
      "expected_impact": "..."
    }
  ],
  "priority_order": ["..."],
  "implementation_roadmap": "..."
}""",
    "HARMONIZATION_EXPERT": """Siz AGENT-4: HARMONIZATION_EXPERT (Muvofiqlashtiruvchi) siz.
Rol: AGENT-3 topgan ziddiyatlar uchun muvofiqlashtirish yechimlarini berasiz.

Faqat JSON formatda javob bering:
{
  "agent": "HARMONIZATION_EXPERT",
  "linked_conflict_id": "...",
  "harmonization_solutions": [
    {
      "conflict_id": "C1",
      "resolution_type": "...",
      "harmonized_text": "...",
      "laws_to_amend": ["...", "..."],
      "laws_to_repeal": ["..."],
      "transitional_provisions": "...",
      "timeline": "..."
    }
  ]
}""",
    "PREDICTOR": """Siz AGENT-5: PREDICTOR (Kelajak Xavflarini Bashoratlovchi) siz.
Rol: Qonun amalga kirgandan so'ng yuzaga kelishi mumkin bo'lgan korrupsion xavflarni bashorat qilasiz.

Faqat JSON formatda javob bering:
{
  "agent": "PREDICTOR",
  "prediction_horizon": "24_months",
  "risk_scenarios": [
    {
      "scenario": "...",
      "probability": 0.75,
      "risk_score": 85,
      "description": "...",
      "early_warning_signs": ["...", "..."],
      "prevention_measures": ["...", "..."]
    }
  ],
  "overall_risk_index": 72,
  "monitoring_recommendations": ["..."]
}""",
    "REPORT_COMPILER": """Siz AGENT-6: REPORT_COMPILER (Hisobot Tuzuvchi) siz.
Rol: Barcha agentlar natijalarini birlashtirasiz va ijroiya uchun yakuniy hisobot tuzasiz.

Faqat JSON formatda javob bering:
{
  "agent": "REPORT_COMPILER",
  "executive_summary": "...",
  "overall_risk_assessment": "...",
  "top_priorities": ["...", "..."],
  "implementation_plan": "...",
  "monitoring_kpis": ["...", "..."]
}"""
}


def read_json_file(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def write_json_file(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def call_anthropic_api(agent_name, input_data, api_key):
    system_prompt = AGENT_PROMPTS.get(agent_name, "")
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 8192,
        "temperature": 0.1,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": "Iltimos, ushbu ma'lumotlarni tahlil qiling: " + json.dumps(input_data, ensure_ascii=False)
            }
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["content"][0]["text"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
    except Exception as e:
        print(f"  [!] Agent {agent_name} xatolik: {e}")
        return {"error": str(e), "agent": agent_name}


def run_analysis(document_text, api_key):
    print("  [1/5] LAW_SCANNER va CONFLICT_DETECTOR ishlamoqda (parallel)...")
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(call_anthropic_api, "LAW_SCANNER", {"document_text": document_text}, api_key)
        f2 = executor.submit(call_anthropic_api, "CONFLICT_DETECTOR", {"document_text": document_text}, api_key)
        scan_result = f1.result()
        conflict_result = f2.result()

    print("  [2/5] SOLUTION_ARCHITECT va HARMONIZATION_EXPERT ishlamoqda (parallel)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f3 = executor.submit(call_anthropic_api, "SOLUTION_ARCHITECT", {"scan_result": scan_result}, api_key)
        f4 = executor.submit(call_anthropic_api, "HARMONIZATION_EXPERT", {"conflict_result": conflict_result}, api_key)
        solution_result = f3.result()
        harmonization_result = f4.result()

    print("  [3/5] PREDICTOR ishlamoqda...")
    prediction_result = call_anthropic_api("PREDICTOR", {"scan": scan_result, "conflicts": conflict_result}, api_key)

    print("  [4/5] REPORT_COMPILER ishlamoqda...")
    compiler_result = call_anthropic_api("REPORT_COMPILER", {
        "scan": scan_result,
        "solutions": solution_result,
        "conflicts": conflict_result,
        "harmonization": harmonization_result,
        "predictions": prediction_result
    }, api_key)

    print("  [5/5] Tahlil yakunlandi!")
    return {
        "scanResult": scan_result,
        "conflictResult": conflict_result,
        "solutionResult": solution_result,
        "harmonizationResult": harmonization_result,
        "predictionResult": prediction_result,
        "compilerResult": compiler_result
    }


class MyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/settings":
            data = read_json_file(SETTINGS_FILE) or {"api_key": ""}
            self._send_json({"api_key": data.get("api_key", "")})
        elif path == "/api/history":
            data = read_json_file(HISTORY_FILE) or []
            self._send_json(data)
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length).decode("utf-8")) if content_length else {}

        if path == "/api/settings":
            write_json_file(SETTINGS_FILE, {"api_key": body.get("api_key", "")})
            self._send_json({"status": "success", "message": "Settings saved"})

        elif path == "/api/analyze":
            api_key = ""
            settings = read_json_file(SETTINGS_FILE)
            if settings:
                api_key = settings.get("api_key", "")
            if not api_key:
                self._send_json({"detail": "API Key topilmadi. Iltimos Sozlamalardan kiriting."}, code=400)
                return
            try:
                document_text = body.get("document_text", "")
                print(f"\n--- Yangi tahlil boshlandi ({len(document_text)} belgi) ---")
                results = run_analysis(document_text, api_key)

                # Save to history
                history = read_json_file(HISTORY_FILE) or []
                new_entry = {
                    "id": str(uuid.uuid4()),
                    "date": datetime.now().isoformat(),
                    "preview_text": document_text[:150] + "...",
                    "full_text": document_text,
                    "results": results
                }
                history.insert(0, new_entry)
                write_json_file(HISTORY_FILE, history)

                self._send_json({"status": "success", "results": results})
            except Exception as e:
                print(f"  [ERROR] {e}")
                self._send_json({"detail": str(e)}, code=500)
        else:
            self._send_json({"detail": "Not Found"}, code=404)

    def _send_json(self, data, code=200):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logs for cleaner console
        pass


if __name__ == "__main__":
    print("=" * 50)
    print("  ANTICORRUPTION AI AGENT SYSTEM")
    print("=" * 50)
    print()
    server = HTTPServer(("127.0.0.1", PORT), MyHandler)
    print(f"  Server ishga tushdi: http://localhost:{PORT}")
    print(f"  To'xtatish uchun: Ctrl+C yoki bu oynani yoping")
    print()

    # Open browser automatically
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server to'xtatildi.")
        server.server_close()
