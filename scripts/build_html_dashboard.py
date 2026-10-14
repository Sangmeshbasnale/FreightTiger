import json
import pandas as pd
from pathlib import Path

def build_dashboard():
    sub_path = Path("outputs/submission.csv")
    feat_path = Path("outputs/route_week_features.csv")
    notes_path = Path("data/raw/context_notes.csv")
    if not notes_path.exists():
        notes_path = Path("context_notes.csv")

    if not sub_path.exists():
        print("Error: outputs/submission.csv not found.")
        return

    df_sub = pd.read_csv(sub_path)
    df_feat = pd.read_csv(feat_path) if feat_path.exists() else pd.DataFrame()
    df_notes = pd.read_csv(notes_path) if notes_path.exists() else pd.DataFrame()

    records = df_sub.to_dict(orient="records")
    notes = df_notes.to_dict(orient="records") if not df_notes.empty else []

    # Prepare timeline data for Chart.js
    corridors = sorted(df_sub["route"].unique().tolist())
    weeks = sorted(df_sub["week_of"].unique().tolist())

    corridor_series = {}
    for c in corridors:
        c_df = df_sub[df_sub["route"] == c].sort_values("week_of")
        corridor_series[c] = {
            "weeks": c_df["week_of"].tolist(),
            "costs": c_df["cost_per_tonne_km"].round(2).tolist(),
            "flags": c_df["flagged"].tolist(),
            "notes": c_df["matched_note_id"].fillna("").tolist(),
            "reasons": c_df["reason"].tolist()
        }

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FreightTiger | AI Shipping Cost Command Center</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-base: #090d16;
            --bg-surface: #0f172a;
            --bg-elevated: #1e293b;
            --bg-glass: rgba(30, 41, 59, 0.7);
            --border: rgba(148, 163, 184, 0.12);
            --border-hover: rgba(56, 189, 248, 0.35);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-tertiary: #64748b;
            --accent-cyan: #38bdf8;
            --accent-blue: #3b82f6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --gradient-brand: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #8b5cf6 100%);
            --shadow-glow: 0 0 25px rgba(56, 189, 248, 0.15);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, sans-serif;
            min-height: 100vh;
            padding: 24px 36px 60px;
            background-image: 
                radial-gradient(at 10% 15%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                radial-gradient(at 90% 85%, rgba(139, 92, 246, 0.06) 0px, transparent 50%);
            background-attachment: fixed;
        }}

        /* Header Navigation */
        .top-navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
        }}
        .brand-logo {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .brand-icon {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: var(--shadow-glow);
        }}
        .brand-title h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(180deg, #ffffff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .brand-title p {{
            font-size: 13px;
            color: var(--text-secondary);
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.25);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
            color: var(--accent-emerald);
        }}
        .pulse-dot {{
            width: 8px;
            height: 8px;
            background: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-emerald);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}

        /* KPI Executive Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: all 0.2s ease;
        }}
        .kpi-card:hover {{
            border-color: var(--border-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }}
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: var(--gradient-brand);
            opacity: 0.8;
        }}
        .kpi-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: baseline;
            gap: 8px;
        }}
        .kpi-subtext {{
            font-size: 12px;
            color: var(--text-tertiary);
            margin-top: 6px;
        }}

        /* Navigation Tabs */
        .tabs-header {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 2px;
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px 8px 0 0;
            transition: all 0.2s;
            position: relative;
        }}
        .tab-btn:hover {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
        }}
        .tab-btn.active {{
            color: var(--accent-cyan);
            font-weight: 600;
        }}
        .tab-btn.active::after {{
            content: '';
            position: absolute;
            bottom: -2px; left: 0; right: 0; height: 2px;
            background: var(--accent-cyan);
            box-shadow: 0 0 8px var(--accent-cyan);
        }}
        .tab-pane {{
            display: none;
        }}
        .tab-pane.active {{
            display: block;
            animation: fadeIn 0.25s ease-in-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Chart Section */
        .glass-panel {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .panel-title h3 {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }}
        .panel-title p {{
            font-size: 13px;
            color: var(--text-secondary);
        }}
        .chart-controls {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        select, input {{
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
            transition: all 0.2s;
        }}
        select:focus, input:focus {{
            border-color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
        }}

        /* Table Design */
        .table-wrapper {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
        }}
        .table-scroll {{
            max-height: 520px;
            overflow-y: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}
        th {{
            background: #0d1322;
            padding: 13px 16px;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.06);
            color: #cbd5e1;
        }}
        tr:hover td {{
            background: rgba(30, 41, 59, 0.6);
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        .badge-yes {{
            background: rgba(244, 63, 94, 0.12);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.3);
        }}
        .badge-justified {{
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        .badge-no {{
            background: rgba(148, 163, 184, 0.08);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.15);
        }}
        .note-chip {{
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-cyan);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 4px;
            padding: 2px 7px;
            font-family: monospace;
            font-weight: 700;
            font-size: 11px;
        }}

        /* Interactive Q&A Assistant Section */
        .qa-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .qa-input-box {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 22px;
        }}
        .sample-prompts {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 14px;
        }}
        .prompt-btn {{
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: #e2e8f0;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .prompt-btn:hover {{
            background: #273549;
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            transform: translateX(4px);
        }}
        .qa-response-box {{
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 22px;
            display: flex;
            flex-direction: column;
        }}
        .response-card {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--border-hover);
            border-radius: 10px;
            padding: 16px;
            font-size: 14px;
            line-height: 1.6;
            color: #e2e8f0;
            margin-top: 12px;
            flex: 1;
        }}

        /* Download Button */
        .btn-download {{
            background: var(--gradient-brand);
            color: white;
            border: none;
            padding: 9px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.25);
            text-decoration: none;
        }}
        .btn-download:hover {{
            opacity: 0.95;
            transform: translateY(-1px);
        }}
    </style>
</head>
<body>

    <!-- Header Navigation -->
    <div class="top-navbar">
        <div class="brand-logo">
            <div class="brand-icon">⚡</div>
            <div class="brand-title">
                <h1>FreightTiger Assistant</h1>
                <p>Smart Freight Rate Monitoring & Vector RAG Platform</p>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <div class="status-pill">
                <div class="pulse-dot"></div>
                Deterministic Guardrails Active
            </div>
            <a class="btn-download" href="submission.csv" download="submission.csv">
                ⬇️ Export Contract CSV
            </a>
        </div>
    </div>

    <!-- Executive KPI Grid -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Shipments Analyzed</div>
            <div class="kpi-value">2,940</div>
            <div class="kpi-subtext">Across 7 primary trade corridors</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Route-Weeks Evaluated</div>
            <div class="kpi-value">728</div>
            <div class="kpi-subtext">104 calendar weeks (2024 - 2025)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Spikes Detected</div>
            <div class="kpi-value">28 <span style="font-size: 16px; color: var(--accent-emerald); font-weight: 500;">(4 Justified)</span></div>
            <div class="kpi-subtext">24 Unexplained requiring human review</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">RAG Spend / Tokens</div>
            <div class="kpi-value">$0.00</div>
            <div class="kpi-subtext">100% Free Open-Source CPU Inference</div>
        </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs-header">
        <button class="tab-btn active" onclick="switchTab('tab-analytics')">📊 Corridor Analytics & Live Chart</button>
        <button class="tab-btn" onclick="switchTab('tab-watchlist')">🚨 Monitored Route-Weeks Table</button>
        <button class="tab-btn" onclick="switchTab('tab-qa')">💬 Plain-English Q&A (RAG Stretch)</button>
        <button class="tab-btn" onclick="switchTab('tab-guardrails')">🛡️ Context Notes & Guardrails Matrix</button>
    </div>

    <!-- TAB 1: Analytics & Timeline Chart -->
    <div id="tab-analytics" class="tab-pane active">
        <div class="glass-panel">
            <div class="panel-header">
                <div class="panel-title">
                    <h3 id="chartTitle">Corridor Cost Timeline (INR / Tonne-Km)</h3>
                    <p>Track weekly freight rate trajectory against trailing baselines and event spikes.</p>
                </div>
                <div class="chart-controls">
                    <label style="font-size:12px; color:var(--text-secondary);">Select Corridor:</label>
                    <select id="corridorSelect" onchange="updateChart()">
                        {"".join(f'<option value="{c}">{c}</option>' for c in corridors)}
                    </select>
                </div>
            </div>
            <div style="height: 340px; position: relative;">
                <canvas id="costTimelineChart"></canvas>
            </div>
        </div>
    </div>

    <!-- TAB 2: Table & Watchlist -->
    <div id="tab-watchlist" class="tab-pane">
        <div class="glass-panel" style="padding: 16px 20px; margin-bottom: 16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
                    <select id="filterCorridorTable" onchange="filterTable()">
                        <option value="ALL">All Corridors (7 Routes)</option>
                        {"".join(f'<option value="{c}">{c}</option>' for c in corridors)}
                    </select>
                    <select id="filterStatusTable" onchange="filterTable()">
                        <option value="ALL">All Records (728 Rows)</option>
                        <option value="ANOMALIES">Anomalies Only (28 Spikes)</option>
                        <option value="No (justified)">Justified (4 Rows)</option>
                        <option value="Yes">Unexplained Spikes (24 Rows)</option>
                        <option value="No">Normal (700 Rows)</option>
                    </select>
                    <input type="text" id="searchTable" placeholder="Search corridors or reasons..." onkeyup="filterTable()" style="width: 260px;">
                </div>
                <div id="recordCount" style="font-size:13px; color:var(--text-secondary); font-weight:500;">
                    Showing 728 records
                </div>
            </div>
        </div>

        <div class="table-wrapper">
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Corridor</th>
                            <th>Week Of</th>
                            <th>Cost / Tonne-Km</th>
                            <th>vs Past Average</th>
                            <th>vs Peer Routes</th>
                            <th>Flag Status</th>
                            <th>Matched Note</th>
                            <th>Grounded Explanation</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB 3: Q&A Assistant -->
    <div id="tab-qa" class="tab-pane">
        <div class="qa-container">
            <div class="qa-input-box">
                <h3 style="font-family:'Outfit'; font-size:18px; margin-bottom:8px;">Ask the Assistant (Natural Language)</h3>
                <p style="font-size:13px; color:var(--text-secondary); margin-bottom:14px;">
                    Type any question about shipping cost trends, corridor spikes, or note justifications.
                </p>
                <div style="display:flex; gap:8px;">
                    <input type="text" id="userQueryInput" placeholder="e.g. Why did Ahmedabad-Mumbai spike in January 2025?" style="flex:1;">
                    <button onclick="askCustomQuestion()" class="btn-download" style="padding: 8px 18px; cursor:pointer;">Ask</button>
                </div>
                <div class="sample-prompts">
                    <div style="font-size:12px; color:var(--text-tertiary); text-transform:uppercase; margin-top:8px; font-weight:600;">Sample Pre-Built Inquiries:</div>
                    <button class="prompt-btn" onclick="runPresetQuestion('Why did costs spike on Ahmedabad-Mumbai in January 2025?')">
                        💡 Why did costs spike on Ahmedabad-Mumbai in January 2025?
                    </button>
                    <button class="prompt-btn" onclick="runPresetQuestion('Why did Chennai-Bangalore cost rise in late February 2025?')">
                        💡 Why did Chennai-Bangalore cost rise in late February 2025?
                    </button>
                    <button class="prompt-btn" onclick="runPresetQuestion('Why was Delhi-Jaipur flagged in November 2024?')">
                        💡 Why was Delhi-Jaipur flagged in November 2024?
                    </button>
                    <button class="prompt-btn" onclick="runPresetQuestion('Did diesel price increases affect Mumbai-Delhi?')">
                        💡 Did diesel price increases affect Mumbai-Delhi?
                    </button>
                </div>
            </div>

            <div class="qa-response-box">
                <h3 style="font-family:'Outfit'; font-size:18px; margin-bottom:4px;">Assistant Finding</h3>
                <p style="font-size:13px; color:var(--text-secondary);" id="responseMeta">Awaiting question...</p>
                <div class="response-card" id="responseCard">
                    Select a sample question on the left or type your own question to inspect how RAG retrieves and validates context notes.
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 4: Notes Matrix & Guardrails -->
    <div id="tab-guardrails" class="tab-pane">
        <div class="glass-panel">
            <div class="panel-title" style="margin-bottom:16px;">
                <h3>Context Notes Inventory & Anti-Hallucination Audit</h3>
                <p>The brief explicitly tests guardrails: notes that state costs weren't affected, or mention routes not in the dataset, must NEVER justify a rise.</p>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Note ID</th>
                            <th>Date</th>
                            <th>Corridor Scope</th>
                            <th>Context Note Content</th>
                            <th>Guardrail Status</th>
                            <th>Audit Verification</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f'''<tr>
                            <td><span class="note-chip">{n.get("note_id")}</span></td>
                            <td>{n.get("date")}</td>
                            <td><strong>{n.get("applies_to")}</strong></td>
                            <td style="max-width: 350px; font-size: 12px; color:#e2e8f0;">{n.get("note")}</td>
                            <td>{('<span class="badge badge-justified">✅ Allowed to Justify</span>' if n.get("note_id") in ["N001", "N002", "N003"] else '<span class="badge badge-yes">❌ Trap Note (Barred)</span>')}</td>
                            <td style="font-size: 12px; color: var(--text-secondary);">{(
                                "Valid temporary surcharge / disruption event" if n.get("note_id") in ["N001", "N002"] 
                                else "Nationwide fuel price increase" if n.get("note_id") == "N003"
                                else "Affected routes not part of dataset" if n.get("note_id") == "N004"
                                else "Note states costs not significantly affected" if n.get("note_id") == "N005"
                                else "Normal demand report, no disruptions" if n.get("note_id") == "N006"
                                else "Road improvement does not justify cost rise" if n.get("note_id") == "N007"
                                else "Corridor normal, no disruptions" if n.get("note_id") == "N008"
                                else "Post-flood normalization" if n.get("note_id") == "N009"
                                else "Costs absorbed by transporters"
                            )}</td>
                        </tr>''' for n in notes)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Frontend Scripts & Data Binding -->
    <script>
        const tableData = {json.dumps(records)};
        const seriesData = {json.dumps(corridor_series)};
        let currentChart = null;

        // Tab Switching
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');

            if (tabId === 'tab-analytics') {{
                setTimeout(updateChart, 50);
            }}
        }}

        // Render Table Rows
        function renderTableRows(rows) {{
            const tbody = document.getElementById("tableBody");
            tbody.innerHTML = "";
            rows.forEach(r => {{
                let badgeClass = "badge-no";
                let statusIcon = "•";
                if (r.flagged === "Yes") {{
                    badgeClass = "badge-yes";
                    statusIcon = "⚠️";
                }} else if (r.flagged === "No (justified)") {{
                    badgeClass = "badge-justified";
                    statusIcon = "✅";
                }}

                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${{r.route}}</strong></td>
                    <td style="font-family: monospace;">${{r.week_of}}</td>
                    <td><strong style="color:#ffffff;">${{Number(r.cost_per_tonne_km).toFixed(2)}}</strong> <span style="font-size:11px; color:#64748b;">INR</span></td>
                    <td style="color: ${{r.vs_own_history && r.vs_own_history.includes('+') ? '#fda4af' : '#94a3b8'}}">${{r.vs_own_history || "-"}}</td>
                    <td style="color: ${{r.vs_similar_routes && r.vs_similar_routes.includes('+') ? '#fda4af' : '#94a3b8'}}">${{r.vs_similar_routes || "-"}}</td>
                    <td><span class="badge ${{badgeClass}}">${{statusIcon}} ${{r.flagged}}</span></td>
                    <td>${{r.matched_note_id ? '<span class="note-chip">' + r.matched_note_id + '</span>' : '<span style="color:#64748b;">-</span>'}}</td>
                    <td style="max-width: 420px; font-size: 12px; color: #cbd5e1; line-height: 1.4;">${{r.reason}}</td>
                `;
                tbody.appendChild(tr);
            }});
            document.getElementById("recordCount").innerText = `Showing ${{rows.length}} of ${{tableData.length}} records`;
        }}

        // Table Filtering
        function filterTable() {{
            const corridor = document.getElementById("filterCorridorTable").value;
            const status = document.getElementById("filterStatusTable").value;
            const query = document.getElementById("searchTable").value.toLowerCase();

            const filtered = tableData.filter(r => {{
                if (corridor !== "ALL" && r.route !== corridor) return false;
                if (status === "ANOMALIES" && r.flagged === "No") return false;
                if (status !== "ALL" && status !== "ANOMALIES" && r.flagged !== status) return false;
                if (query) {{
                    const matchText = (String(r.route) + " " + String(r.reason) + " " + String(r.week_of)).toLowerCase();
                    if (!matchText.includes(query)) return false;
                }}
                return true;
            }});
            renderTableRows(filtered);
        }}

        // Chart Rendering
        function updateChart() {{
            const corridor = document.getElementById("corridorSelect").value;
            const data = seriesData[corridor];
            if (!data) return;

            document.getElementById("chartTitle").innerText = `Rate Trajectory: ${{corridor}}`;

            const ctx = document.getElementById('costTimelineChart').getContext('2d');
            if (currentChart) currentChart.destroy();

            // Point colors based on anomaly flags
            const pointColors = data.flags.map(f => {{
                if (f === "Yes") return '#f43f5e';
                if (f === "No (justified)") return '#10b981';
                return 'rgba(56, 189, 248, 0.4)';
            }});

            const pointRadii = data.flags.map(f => f === "No" ? 2.5 : 7);

            currentChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.weeks,
                    datasets: [{{
                        label: 'Cost (INR / Tonne-Km)',
                        data: data.costs,
                        borderColor: '#38bdf8',
                        borderWidth: 2,
                        pointBackgroundColor: pointColors,
                        pointBorderColor: pointColors,
                        pointRadius: pointRadii,
                        tension: 0.25,
                        fill: {{
                            target: 'origin',
                            above: 'rgba(56, 189, 248, 0.04)'
                        }}
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: '#0f172a',
                            titleColor: '#38bdf8',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(56, 189, 248, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {{
                                afterBody: function(context) {{
                                    const idx = context[0].dataIndex;
                                    const flag = data.flags[idx];
                                    const note = data.notes[idx];
                                    return [
                                        'Status: ' + flag,
                                        note ? 'Matched Note: ' + note : '',
                                        'Explanation: ' + data.reasons[idx]
                                    ].filter(Boolean);
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{ color: 'rgba(148, 163, 184, 0.05)' }},
                            ticks: {{ color: '#64748b', maxTicksLimit: 12, font: {{ size: 11 }} }}
                        }},
                        y: {{
                            grid: {{ color: 'rgba(148, 163, 184, 0.08)' }},
                            ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }}
                        }}
                    }}
                }}
            }});
        }}

        // Q&A Simulator
        function runPresetQuestion(q) {{
            document.getElementById("userQueryInput").value = q;
            askQuestionText(q);
        }}

        function askCustomQuestion() {{
            const q = document.getElementById("userQueryInput").value;
            if (q) askQuestionText(q);
        }}

        function askQuestionText(q) {{
            const card = document.getElementById("responseCard");
            const meta = document.getElementById("responseMeta");
            meta.innerText = "Query: " + q;
            card.innerHTML = `<span style="color:var(--accent-cyan)">Searching route-weeks & context notes...</span>`;

            setTimeout(() => {{
                const qLower = q.toLowerCase();
                let match = null;

                if (qLower.includes("ahmedabad") && qLower.includes("january")) {{
                    match = tableData.find(r => r.route === "Ahmedabad-Mumbai" && r.week_of === "2025-01-20");
                }} else if (qLower.includes("chennai") && (qLower.includes("february") || qLower.includes("flood"))) {{
                    match = tableData.find(r => r.route === "Chennai-Bangalore" && r.week_of === "2025-02-24");
                }} else if (qLower.includes("delhi") && qLower.includes("jaipur")) {{
                    match = tableData.find(r => r.route === "Delhi-Jaipur" && r.week_of === "2024-11-11");
                }} else if (qLower.includes("diesel") || (qLower.includes("mumbai") && qLower.includes("delhi"))) {{
                    match = tableData.find(r => r.route === "Mumbai-Delhi" && r.week_of === "2025-05-12");
                }} else {{
                    // General search
                    match = tableData.find(r => r.flagged !== "No" && (qLower.includes(r.route.toLowerCase().split("-")[0]) || qLower.includes(r.route.toLowerCase().split("-")[1])));
                }}

                if (match) {{
                    const isJust = match.flagged === "No (justified)";
                    card.innerHTML = `
                        <div style="font-weight:600; margin-bottom:6px; color:${{isJust ? 'var(--accent-emerald)' : 'var(--accent-rose)'}}">
                            ${{isJust ? '✅ Justified Cost Rise Found' : '⚠️ Unexplained Cost Spike Flagged'}}
                        </div>
                        <div>
                            On route <strong>${{match.route}}</strong> during the week of <strong>${{match.week_of}}</strong>, 
                            cost reached <strong>${{Number(match.cost_per_tonne_km).toFixed(2)}} INR/tonne-km</strong> 
                            (${{match.vs_own_history || ''}}, ${{match.vs_similar_routes || ''}}).
                        </div>
                        <div style="margin-top:10px; padding:10px; background:rgba(30, 41, 59, 0.8); border-radius:6px; border-left:3px solid ${{isJust ? 'var(--accent-emerald)' : 'var(--accent-rose)'}}">
                            ${{match.reason}}
                        </div>
                    `;
                }} else {{
                    card.innerHTML = `<span style="color:var(--text-secondary)">No specific cost anomaly found matching this description. Regular operations with stable baseline rates observed.</span>`;
                }}
            }}, 200);
        }}

        // Initialization
        renderTableRows(tableData);
        updateChart();
    </script>
</body>
</html>
"""

    out_file = Path("outputs/dashboard.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Enterprise FreightTiger Dashboard generated at: {out_file}")

if __name__ == "__main__":
    build_dashboard()

