def enforce_drift_gate(psi_by_feature: dict[str, float], maximum_psi: float) -> None:
    if not psi_by_feature:
        raise ValueError("psi_by_feature must not be empty")
    drifted_features = {
        feature_name: psi
        for feature_name, psi in psi_by_feature.items()
        if psi >= maximum_psi
    }
    if drifted_features:
        raise ValueError(
            f"data drift detected: {drifted_features} (psi threshold {maximum_psi})"
        )
