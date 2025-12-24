
import asyncio
import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock

sys.path.append(os.getcwd())

from council.mcp.ai_council_server import AICouncilServer, ModelProvider, ModelResponse
from council.facilitator.wald_consensus import ConsensusDecision

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Council - Semantic Entropy Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #334155; }
        h1 { color: #38bdf8; }
        h2 { border-bottom: 1px solid #334155; padding-bottom: 10px; font-size: 1.2rem; }
        canvas { max-height: 300px; }
        .metrics-row { display: flex; gap: 20px; }
        .metric-box { flex: 1; text-align: center; }
        .metric-value { font-size: 2rem; font-weight: bold; }
        .high-entropy { color: #f43f5e; }
        .low-entropy { color: #10b981; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 AI Council Semantic Entropy Monitor</h1>
        
        <div class="metrics-row">
            <div class="card metric-box">
                <h2>Average Entropy</h2>
                <div class="metric-value" id="avgEntropy">--</div>
            </div>
            <div class="card metric-box">
                <h2>Consensus Rate</h2>
                <div class="metric-value" id="consensusRate">--</div>
            </div>
        </div>

        <div class="card">
            <h2>📉 Entropy Trend (Confusion Level)</h2>
            <canvas id="entropyChart"></canvas>
            <p style="font-size: 0.9rem; color: #94a3b8; margin-top: 10px;">
                Low Entropy (0.0) means Models fully agree (Correct). High Entropy (~1.0) means Models are confused/split.
            </p>
        </div>

        <div class="card">
            <h2>🎯 Wald Consensus Probability (Pi)</h2>
            <canvas id="waldChart"></canvas>
        </div>
    </div>

    <script>
        const data = {{DATA_JSON}};
        
        // Calculate Summary Metrics
        const avgEntropy = data.entropy.reduce((a, b) => a + b, 0) / data.entropy.length;
        const consensusCount = data.wald_pi.filter(p => p > 0.9 || p < 0.2).length;
        const consensusRate = Math.round((consensusCount / data.wald_pi.length) * 100) + "%";
        
        document.getElementById('avgEntropy').innerText = avgEntropy.toFixed(3);
        document.getElementById('avgEntropy').className = "metric-value " + (avgEntropy > 0.6 ? "high-entropy" : "low-entropy");
        document.getElementById('consensusRate').innerText = consensusRate;

        // Entropy Chart
        new Chart(document.getElementById('entropyChart'), {
            type: 'line',
            data: {
                labels: data.timestamps,
                datasets: [{
                    label: 'Semantic Entropy (H)',
                    data: data.entropy,
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    y: { min: 0, max: 1.0, grid: { color: '#334155' } },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });

        // Wald Chart
        new Chart(document.getElementById('waldChart'), {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Consensus Probability (Pi)',
                    data: data.wald_pi,
                    backgroundColor: data.wald_pi.map(v => v > 0.9 ? '#10b981' : (v < 0.3 ? '#ef4444' : '#f59e0b')),
                }]
            },
            options: {
                scales: {
                    y: { min: 0, max: 1.0, grid: { color: '#334155' } },
                    x: { ticks: { display: false } } // Hide long labels
                }
            }
        });
    </script>
</body>
</html>
"""

async def generate_simulation():
    server = AICouncilServer(models=[])
    
    # We mock _query_model to control the output logic for specific entropy scenarios
    server._query_model = AsyncMock()
    server._synthesize_responses = AsyncMock(return_value="Synthesized.")
    server.gateway = MagicMock()
    server.gateway._scan_content.return_value = 0 # OK Risk
    
    print("Running Simulation Scenarios...")
    
    # Scenario 1: High Consensus (Everybody Approves) -> Low Entropy
    server._query_model.return_value = ModelResponse(
        provider=ModelProvider.GEMINI, model_name="mock", content="Vote: APPROVE\nConfidence: 0.99", latency_ms=10, success=True
    )
    # We need to simulate multiple responses for parallel query, wait...
    # Actually query_parallel calls _query_model multiple times.
    # Let's mock query_parallel directly to make it easier to control the batch result
    
    server.query_parallel = AsyncMock()
    
    print("1. Scenario: Perfect Agreement (Low Entropy)")
    server.query_parallel.return_value = [
        ModelResponse(ModelProvider.GEMINI, "gemini", "Vote: APPROVE\nConfidence: 0.99", 50, True),
        ModelResponse(ModelProvider.OPENAI, "gpt-4", "Vote: APPROVE\nConfidence: 0.98", 60, True),
    ]
    await server.query("Is Python a programming language?")
    
    print("2. Scenario: Slight Disagreement (Low-Mid Entropy)")
    server.query_parallel.return_value = [
        ModelResponse(ModelProvider.GEMINI, "gemini", "Vote: APPROVE\nConfidence: 0.80", 50, True),
        ModelResponse(ModelProvider.OPENAI, "gpt-4", "Vote: APPROVE\nConfidence: 0.60", 60, True),
    ]
    await server.query("Is C++ hard?")

    print("3. Scenario: Total Confusion (High Entropy)")
    server.query_parallel.return_value = [
        ModelResponse(ModelProvider.GEMINI, "gemini", "Vote: APPROVE\nConfidence: 0.9", 50, True),
        ModelResponse(ModelProvider.OPENAI, "gpt-4", "Vote: REJECT\nConfidence: 0.9", 60, True),
    ]
    await server.query("Should we deploy to prod on Friday?")

    print("4. Scenario: Strong Rejection (Low Entropy)")
    server.query_parallel.return_value = [
        ModelResponse(ModelProvider.GEMINI, "gemini", "Vote: REJECT\nConfidence: 0.99", 50, True),
        ModelResponse(ModelProvider.OPENAI, "gpt-4", "Vote: REJECT\nConfidence: 0.95", 60, True),
    ]
    await server.query("Delete the database?")

    # Generate HTML
    stats = server.monitor.get_stats()
    json_data = json.dumps(stats)
    html = DASHBOARD_TEMPLATE.replace("{{DATA_JSON}}", json_data)
    
    with open("dashboard.html", "w") as f:
        f.write(html)
        
    print(f"\nDashboard generated at: {os.path.abspath('dashboard.html')}")
    print(f"Stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(generate_simulation())
