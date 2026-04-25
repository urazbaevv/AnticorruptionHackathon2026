const AGENT_PROMPTS = {
    "LAW_SCANNER": `Siz O'zbekiston Respublikasining qonun hujjatlarini tahlil qiluvchi AGENT-1: LAW_SCANNER (Qonun Bo'shliqlarini Topuvchi) siz.
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
}`,
    
    "CONFLICT_DETECTOR": `Siz AGENT-3: CONFLICT_DETECTOR (Qarama-qarshilik Topuvchi) siz.
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
}`,
    
    "SOLUTION_ARCHITECT": `Siz AGENT-2: SOLUTION_ARCHITECT (Yechim Yaratuvchi) siz.
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
}`,

    "HARMONIZATION_EXPERT": `Siz AGENT-4: HARMONIZATION_EXPERT (Muvofiqlashtiruvchi) siz.
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
}`,

    "PREDICTOR": `Siz AGENT-5: PREDICTOR (Kelajak Xavflarini Bashoratlovchi) siz.
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
}`,

    "REPORT_COMPILER": `Siz AGENT-6: REPORT_COMPILER (Hisobot Tuzuvchi) siz.
Rol: Barcha agentlar natijalarini birlashtirasiz va ijroiya uchun yakuniy Markdown/JSON hisobot tuzasiz.

Faqat JSON formatda javob bering:
{
  "agent": "REPORT_COMPILER",
  "executive_summary": "...",
  "overall_risk_assessment": "...",
  "top_priorities": ["...", "..."],
  "implementation_plan": "...",
  "monitoring_kpis": ["...", "..."]
}`
};

async function runAgent(agentName, inputData, apiKey) {
    const systemPrompt = AGENT_PROMPTS[agentName] || "";
    
    const payload = {
        model: "claude-3-5-sonnet-20240620",
        max_tokens: 8192,
        temperature: 0.1,
        system: systemPrompt,
        messages: [
            {
                role: "user",
                content: "Iltimos, ushbu ma'lumotlarni tahlil qiling: " + JSON.stringify(inputData)
            }
        ]
    };
    
    try {
        const response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
                "x-api-key": apiKey,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errBody = await response.text();
            throw new Error(`API Error: ${response.status} - ${errBody}`);
        }

        const data = await response.json();
        let content = data.content[0].text;
        
        // Extract JSON
        if (content.includes("```json")) {
            content = content.split("```json")[1].split("```")[0];
        } else if (content.includes("```")) {
            content = content.split("```")[1].split("```")[0];
        }
            
        return JSON.parse(content.trim());
    } catch (e) {
        console.error(`Error running agent ${agentName}:`, e.message);
        return { error: e.message, agent: agentName, mock_data: true };
    }
}

async function runAnticorruptionAnalysis(documentText, apiKey) {
    // STEP 1 & 2: Parallel run
    const [scanResult, conflictResult] = await Promise.all([
        runAgent("LAW_SCANNER", { document_text: documentText }, apiKey),
        runAgent("CONFLICT_DETECTOR", { document_text: documentText }, apiKey)
    ]);
    
    // STEP 3: Parallel run
    const [solutionResult, harmonizationResult] = await Promise.all([
        runAgent("SOLUTION_ARCHITECT", { scan_result: scanResult }, apiKey),
        runAgent("HARMONIZATION_EXPERT", { conflict_result: conflictResult }, apiKey)
    ]);
    
    // STEP 4
    const predictionResult = await runAgent("PREDICTOR", {
        scan: scanResult,
        conflicts: conflictResult
    }, apiKey);
    
    // STEP 5
    const compilerResult = await runAgent("REPORT_COMPILER", {
        scan: scanResult,
        solutions: solutionResult,
        conflicts: conflictResult,
        harmonization: harmonizationResult,
        predictions: predictionResult
    }, apiKey);
    
    return {
        scanResult,
        conflictResult,
        solutionResult,
        harmonizationResult,
        predictionResult,
        compilerResult
    };
}

module.exports = {
    runAnticorruptionAnalysis
};
