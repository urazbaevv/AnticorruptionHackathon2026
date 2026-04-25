import httpx
import json
import asyncio

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
Rol: Barcha agentlar natijalarini birlashtirasiz va ijroiya uchun yakuniy Markdown/JSON hisobot tuzasiz.

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

async def run_agent(agent_name: str, input_data: dict, api_key: str):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = AGENT_PROMPTS.get(agent_name, "")
    
    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 8192,
        "temperature": 0.1,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": "Iltimos, ushbu ma'lumotlarni tahlil qiling: " + json.dumps(input_data, ensure_ascii=False)
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]
            
            # Extract JSON from potential markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            return json.loads(content.strip())
        except Exception as e:
            print(f"Error running agent {agent_name}: {str(e)}")
            # Mock mode fallback if API key is invalid or errors out (Useful for demo/Hakaton)
            return {"error": str(e), "agent": agent_name, "mock_data": True}

async def run_anticorruption_analysis(document_text: str, api_key: str):
    # STEP 1 & 2: Parallel run of LAW_SCANNER and CONFLICT_DETECTOR
    task_scanner = asyncio.create_task(run_agent("LAW_SCANNER", {"document_text": document_text}, api_key))
    task_conflict = asyncio.create_task(run_agent("CONFLICT_DETECTOR", {"document_text": document_text}, api_key))
    
    scan_result, conflict_result = await asyncio.gather(task_scanner, task_conflict)
    
    # STEP 3: Parallel run of SOLUTION_ARCHITECT and HARMONIZATION_EXPERT
    task_solution = asyncio.create_task(run_agent("SOLUTION_ARCHITECT", {"scan_result": scan_result}, api_key))
    task_harmonize = asyncio.create_task(run_agent("HARMONIZATION_EXPERT", {"conflict_result": conflict_result}, api_key))
    
    solution_result, harmonization_result = await asyncio.gather(task_solution, task_harmonize)
    
    # STEP 4: PREDICTOR
    prediction_result = await run_agent("PREDICTOR", {
        "scan": scan_result,
        "conflicts": conflict_result
    }, api_key)
    
    # STEP 5: REPORT_COMPILER
    compiler_result = await run_agent("REPORT_COMPILER", {
        "scan": scan_result,
        "solutions": solution_result,
        "conflicts": conflict_result,
        "harmonization": harmonization_result,
        "predictions": prediction_result
    }, api_key)
    
    return {
        "scanResult": scan_result,
        "conflictResult": conflict_result,
        "solutionResult": solution_result,
        "harmonizationResult": harmonization_result,
        "predictionResult": prediction_result,
        "compilerResult": compiler_result
    }
