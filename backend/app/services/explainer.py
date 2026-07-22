class Explainer:
    @staticmethod
    def generate_explanation(
        track_id: int,
        label: str,
        risk_score: int,
        threat_level: str,
        triggers: list,
        speed: float,
        dwell_time: float,
        zone_name: str = "Restricted Zone"
    ) -> str:
        """
        Generates an explainable text summary detailing the reason for a given risk assessment.
        """
        if risk_score < 30:
            return f"The subject ({label} #{track_id}) is behaving normally. Speed: {speed:.1f} px/s. No active zone breaches."
            
        explanation = (
            f"AI Decision Engine flagged subject {label} #{track_id} with a threat level of "
            f"'{threat_level}' (Risk Score: {risk_score}/100). "
        )
        
        # Details of triggers
        trigger_reasons = []
        if "Restricted zone breach" in triggers:
            trigger_reasons.append(f"breaching the restricted area '{zone_name}'")
        if any("Loitering" in t for t in triggers):
            trigger_reasons.append(f"loitering inside the zone for {int(dwell_time)} seconds")
        if "Rapid movement (running)" in triggers:
            trigger_reasons.append(f"moving at a high velocity ({speed:.1f} px/s) inside the zone")
            
        if trigger_reasons:
            explanation += f"This assessment is driven by the subject " + ", and ".join(trigger_reasons) + ". "
        else:
            explanation += f"The subject is currently inside the monitored area with a dwell time of {int(dwell_time)}s. "
            
        # Contextual explanation (Explainable AI reasoning)
        if speed > 120.0:
            explanation += "The high velocity indicates running or rushing behavior, suggesting a potential intrusion or fleeing attempt."
        elif speed < 15.0 and dwell_time > 0:
            explanation += "The low velocity suggests stationary presence, indicating the subject may be staking out the area or waiting in a prohibited zone."
        else:
            explanation += f"The subject is traversing the zone at a normal pace ({speed:.1f} px/s)."
            
        return explanation
