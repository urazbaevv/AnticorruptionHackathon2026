const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const { runAnticorruptionAnalysis } = require('./agents');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'static')));

const DATA_DIR = path.join(__dirname, 'data');
const SETTINGS_FILE = path.join(DATA_DIR, 'settings.json');
const HISTORY_FILE = path.join(DATA_DIR, 'history.json');

// Ensure data dir exists
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

app.get('/api/settings', (req, res) => {
    try {
        if (fs.existsSync(SETTINGS_FILE)) {
            const data = JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
            return res.json({ api_key: data.api_key || "" });
        }
    } catch (e) {
        console.error("Error reading settings", e);
    }
    res.json({ api_key: "" });
});

app.post('/api/settings', (req, res) => {
    try {
        const { api_key } = req.body;
        fs.writeFileSync(SETTINGS_FILE, JSON.stringify({ api_key }));
        res.json({ status: "success", message: "Settings saved successfully" });
    } catch (e) {
        res.status(500).json({ detail: e.message });
    }
});

app.get('/api/history', (req, res) => {
    try {
        if (fs.existsSync(HISTORY_FILE)) {
            const data = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
            return res.json(data);
        }
    } catch (e) {
        console.error("Error reading history", e);
    }
    res.json([]);
});

app.post('/api/analyze', async (req, res) => {
    try {
        const { document_text } = req.body;
        let api_key = "";
        
        if (fs.existsSync(SETTINGS_FILE)) {
            const data = JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
            api_key = data.api_key || "";
        }
            
        if (!api_key) {
            return res.status(400).json({ detail: "API Key is missing. Please set it in Settings." });
        }
        
        const results = await runAnticorruptionAnalysis(document_text, api_key);
        
        // Save to history
        let history = [];
        if (fs.existsSync(HISTORY_FILE)) {
            try {
                history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
            } catch (e) {}
        }
                
        const new_entry = {
            id: uuidv4(),
            date: new Date().toISOString(),
            preview_text: document_text.substring(0, 150) + "...",
            full_text: document_text,
            results: results
        };
        history.unshift(new_entry); // Add to top
        
        fs.writeFileSync(HISTORY_FILE, JSON.stringify(history));
            
        res.json({ status: "success", results: results });
    } catch (e) {
        console.error("Analysis Error:", e);
        res.status(500).json({ detail: e.message || "Xatolik yuz berdi" });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on http://127.0.0.1:${PORT}`);
    console.log(`Press CTRL+C to stop.`);
});
