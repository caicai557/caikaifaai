
import math
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from council.facilitator.wald_consensus import ConsensusResult, ConsensusDecision

@dataclass
class MetricPoint:
    timestamp: datetime
    query_preview: str
    wald_pi: float
    entropy: float
    decision: str
    latency_ms: float

class SemanticEntropyMonitor:
    """
    Monitors the 'Semantic Entropy' of the AI Council.
    
    Entropy (H) is calculated based on the Wald Probability (pi).
    H = -(pi * log2(pi) + (1-pi) * log2(1-pi))
    
    H -> 0: High certainty (Consensus)
    H -> 1: High uncertainty (Confusion)
    """
    
    def __init__(self):
        self.history: List[MetricPoint] = []
        
    def _calculate_binary_entropy(self, pi: float) -> float:
        """Calculate logical entropy of the consensus probability"""
        # Clip to avoid domain errors
        p = max(0.0001, min(0.9999, pi))
        return -(p * math.log2(p) + (1-p) * math.log2(1-p))

    def log_response(self, query: str, wald_result: ConsensusResult, latency_ms: float) -> None:
        """Log a new consensus event"""
        entropy = self._calculate_binary_entropy(wald_result.pi_approve)
        
        point = MetricPoint(
            timestamp=datetime.now(),
            query_preview=query[:30] + "..." if len(query) > 30 else query,
            wald_pi=wald_result.pi_approve,
            entropy=entropy,
            decision=wald_result.decision.value,
            latency_ms=latency_ms
        )
        self.history.append(point)
        
    def get_stats(self) -> Dict[str, Any]:
        """Return formatted stats for dashboard"""
        return {
            "timestamps": [p.timestamp.strftime("%H:%M:%S") for p in self.history],
            "entropy": [round(p.entropy, 3) for p in self.history],
            "wald_pi": [round(p.wald_pi, 3) for p in self.history],
            "labels": [f"{p.query_preview} ({p.decision})" for p in self.history],
            "latency": [round(p.latency_ms, 0) for p in self.history]
        }
        
    def clear(self):
        self.history = []
