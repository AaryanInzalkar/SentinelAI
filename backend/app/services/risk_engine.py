import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier

class RiskEngine:
    def __init__(self):
        self.model = None
        self._initialize_ml_model()

    def _initialize_ml_model(self):
        """
        Train a lightweight Scikit-Learn Random Forest model on simulated threat vectors on startup.
        Features: [speed_px_sec, dwell_time_sec, is_in_restricted_zone (0 or 1)]
        Labels: 0 (Normal), 1 (Suspicious/Threat)
        """
        try:
            # Generate synthetic training dataset
            # Columns: [speed, dwell_time, is_restricted]
            X = []
            y = []
            
            # Normal behaviors (Class 0)
            # Low dwell time, high or low speed, outside restricted zone
            for _ in range(50):
                X.append([np.random.uniform(5, 50), np.random.uniform(0, 4), 0])
                y.append(0)
            # Fast passerby outside zone
            for _ in range(25):
                X.append([np.random.uniform(100, 200), np.random.uniform(0, 2), 0])
                y.append(0)
                
            # Suspicious behaviors (Class 1)
            # Long dwell time inside restricted zone
            for _ in range(40):
                X.append([np.random.uniform(0, 15), np.random.uniform(10, 40), 1])
                y.append(1)
            # High speed inside restricted zone (running intrusion)
            for _ in range(25):
                X.append([np.random.uniform(120, 250), np.random.uniform(1, 5), 1])
                y.append(1)
                
            X = np.array(X)
            y = np.array(y)
            
            # Train Random Forest
            self.model = RandomForestClassifier(n_estimators=10, random_state=42)
            self.model.fit(X, y)
            print("RiskEngine ML Model (RandomForest) initialized and trained successfully.")
        except Exception as e:
            print(f"Error training RiskEngine ML model: {e}. Falling back to heuristic scoring.")
            self.model = None

    def evaluate_threats(
        self, 
        tracked_objects: List[Dict[str, Any]], 
        loitering_threshold: int
    ) -> List[Dict[str, Any]]:
        """
        Evaluates risk score for each tracked object.
        Returns objects annotated with 'risk_score', 'threat_level' (Low, Medium, High), and triggered triggers.
        """
        evaluated_objects = []
        
        for obj in tracked_objects:
            track_id = obj["track_id"]
            speed = obj.get("speed", 0.0)
            active_zones = obj.get("active_zones", {})
            
            in_restricted = any(z["is_restricted"] for z in active_zones.values())
            max_dwell_time = max([z["dwell_time"] for z in active_zones.values()], default=0.0)
            
            # 1. Compute ML Risk Probability
            ml_risk_prob = 0.0
            if self.model is not None:
                try:
                    # Feature vector: [speed, dwell_time, is_restricted]
                    features = [[speed, max_dwell_time, 1.0 if in_restricted else 0.0]]
                    ml_risk_prob = float(self.model.predict_proba(features)[0][1])
                except Exception as e:
                    print(f"Prediction error for track {track_id}: {e}")
                    
            # 2. Compute Heuristic score as safety/fallback buffer
            heuristic_score = 0
            triggers = []
            
            if in_restricted:
                heuristic_score += 30
                triggers.append("Restricted zone breach")
                
                # Check loitering
                if max_dwell_time >= loitering_threshold:
                    heuristic_score += 40
                    triggers.append(f"Loitering detected ({int(max_dwell_time)}s)")
                    
                    # Extra penalty for prolonged loitering
                    overtime = max_dwell_time - loitering_threshold
                    heuristic_score += min(20, int(overtime * 1.5))
                
                # Check rapid movement in restricted zone
                if speed > 100.0:
                    heuristic_score += 15
                    triggers.append("Rapid movement (running)")
            
            # Combine ML probability and heuristics (weighted average)
            ml_score = int(ml_risk_prob * 100)
            if self.model is not None:
                # 70% ML score, 30% heuristic score for robust behavior
                final_score = int(0.7 * ml_score + 0.3 * heuristic_score)
            else:
                final_score = heuristic_score
                
            final_score = min(100, max(0, final_score))
            
            # Determine threat level
            if final_score >= 70:
                threat_level = "Critical"
            elif final_score >= 40:
                threat_level = "Warning"
            else:
                threat_level = "Low"
                
            eval_obj = obj.copy()
            eval_obj["risk_score"] = final_score
            eval_obj["threat_level"] = threat_level
            eval_obj["triggers"] = triggers
            evaluated_objects.append(eval_obj)
            
        return evaluated_objects
