document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const apiKeyInput = document.getElementById('apiKeyInput');

    const inputSection = document.getElementById('inputSection');
    const documentInput = document.getElementById('documentInput');
    const analyzeBtn = document.getElementById('analyzeBtn');

    const loadingSection = document.getElementById('loadingSection');
    const progressBar = document.getElementById('progressBar');
    
    const resultsSection = document.getElementById('resultsSection');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');

    // Load Settings on start
    fetchSettings();

    // Modal Events
    settingsBtn.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
    });

    closeSettingsBtn.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });

    saveSettingsBtn.addEventListener('click', async () => {
        const key = apiKeyInput.value.trim();
        await saveSettings(key);
        settingsModal.classList.add('hidden');
        alert("Sozlamalar saqlandi!");
    });

    // Analysis Event
    analyzeBtn.addEventListener('click', async () => {
        const text = documentInput.value.trim();
        if (!text) {
            alert("Iltimos, tahlil qilish uchun qonun matnini kiriting!");
            return;
        }

        // 1. Hide input, show loading
        inputSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        
        // Setup mock progress animation
        runProgressAnimation();

        try {
            // 2. Call backend
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ document_text: text })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "API Xatolik!");
            }

            const data = await response.json();
            
            // 3. Render results
            renderResults(data.results);

        } catch (error) {
            alert("Xatolik yuz berdi: " + error.message);
            // Revert UI
            loadingSection.classList.add('hidden');
            inputSection.classList.remove('hidden');
        }
    });

    newAnalysisBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
        documentInput.value = '';
        resetProgress();
    });

    // API Functions
    async function fetchSettings() {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            if (data.api_key) {
                apiKeyInput.value = data.api_key;
            }
        } catch (e) {
            console.error("Sozlamalarni yuklashda xatolik", e);
        }
    }

    async function saveSettings(key) {
        try {
            await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key })
            });
        } catch (e) {
            console.error("Sozlamalarni saqlashda xatolik", e);
        }
    }

    // UI Functions
    function runProgressAnimation() {
        const steps = [
            'step-scanner',
            'step-conflict',
            'step-solution',
            'step-harmonization',
            'step-predictor',
            'step-compiler'
        ];
        
        let currentStep = 0;
        let progress = 0;

        const interval = setInterval(() => {
            progress += 2;
            progressBar.style.width = `${progress}%`;

            if (progress === 10) activateStep(steps[0]);
            if (progress === 30) { finishStep(steps[0]); activateStep(steps[1]); activateStep(steps[2]); }
            if (progress === 60) { finishStep(steps[1]); finishStep(steps[2]); activateStep(steps[3]); activateStep(steps[4]); }
            if (progress === 85) { finishStep(steps[3]); finishStep(steps[4]); activateStep(steps[5]); }
            
            // Note: Actual transition is handled by await fetch returning. This is just visual feedback.
            if (progress >= 95) {
                clearInterval(interval);
            }
        }, 100);

        // Store interval to clear it later if needed
        window.progressInterval = interval;
    }

    function activateStep(id) {
        const el = document.getElementById(id);
        if(el) {
            el.classList.add('active');
            el.querySelector('.spinner').classList.remove('hidden');
            el.querySelector('i').classList.add('hidden');
        }
    }

    function finishStep(id) {
        const el = document.getElementById(id);
        if(el) {
            el.classList.remove('active');
            el.classList.add('done');
            el.querySelector('.spinner').classList.add('hidden');
            el.querySelector('i').classList.remove('hidden');
            el.querySelector('i').className = 'fa-solid fa-check';
        }
    }

    function resetProgress() {
        progressBar.style.width = '0%';
        const steps = document.querySelectorAll('.agent-step');
        steps.forEach(step => {
            step.classList.remove('active', 'done');
            step.querySelector('.spinner').classList.add('hidden');
            step.querySelector('i').classList.remove('hidden');
            // Reset icons
            const icon = step.querySelector('i');
            if(step.id === 'step-scanner') icon.className = 'fa-solid fa-magnifying-glass';
            if(step.id === 'step-conflict') icon.className = 'fa-solid fa-scale-balanced';
            if(step.id === 'step-solution') icon.className = 'fa-solid fa-lightbulb';
            if(step.id === 'step-harmonization') icon.className = 'fa-solid fa-handshake';
            if(step.id === 'step-predictor') icon.className = 'fa-solid fa-crystal-ball';
            if(step.id === 'step-compiler') icon.className = 'fa-solid fa-file-invoice';
        });
    }

    function renderResults(results) {
        if (window.progressInterval) clearInterval(window.progressInterval);
        progressBar.style.width = '100%';
        
        // Hide loading after a short delay
        setTimeout(() => {
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            
            // Populate data
            const compiler = results.compilerResult || {};
            const predictor = results.predictionResult || {};
            const scanner = results.scanResult || {};

            // Executive Summary
            document.getElementById('res-exec-summary').textContent = 
                compiler.executive_summary || "Tahlil natijalari (Mock data: API kaliti orqali ulansangiz haqiqiy hisobot chiqadi).";

            // Risk Score
            const riskScore = predictor.overall_risk_index || 0;
            const circle = document.querySelector('.risk-score-circle');
            document.getElementById('res-risk-score').textContent = riskScore;
            
            let riskColor = 'var(--success)';
            if(riskScore > 40) riskColor = 'var(--warning)';
            if(riskScore > 75) riskColor = 'var(--danger)';
            circle.style.background = `conic-gradient(${riskColor} ${riskScore}%, rgba(255,255,255,0.1) 0)`;

            // Priorities
            const prioritiesList = document.getElementById('res-priorities');
            prioritiesList.innerHTML = '';
            const priorities = compiler.top_priorities || ["1-moddani aniqlashtirish", "Korrupsion xavfni yo'qotish"];
            priorities.forEach(p => {
                const li = document.createElement('li');
                li.textContent = p;
                prioritiesList.appendChild(li);
            });

            // Vulnerabilities Table
            const vulns = scanner.vulnerabilities || [];
            const tableContainer = document.getElementById('res-vulnerabilities');
            if (vulns.length > 0) {
                let html = `<table>
                    <thead>
                        <tr>
                            <th>Modda</th>
                            <th>Xavf Darajasi</th>
                            <th>Muammo turi</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                vulns.forEach(v => {
                    let badgeClass = 'badge-orta';
                    if(v.risk_level === 'KRITIK') badgeClass = 'badge-kritik';
                    if(v.risk_level === 'YUQORI') badgeClass = 'badge-yuqori';

                    html += `<tr>
                        <td>${v.article}</td>
                        <td><span class="badge ${badgeClass}">${v.risk_level}</span></td>
                        <td>${v.vulnerability_type}</td>
                    </tr>`;
                });
                
                html += `</tbody></table>`;
                tableContainer.innerHTML = html;
            } else {
                tableContainer.innerHTML = "<p>Hech qanday bo'shliq topilmadi yoki bu Mock rejim.</p>";
            }

            // Raw JSON
            document.getElementById('res-json-raw').textContent = JSON.stringify(results, null, 2);

        }, 500);
    }
});
