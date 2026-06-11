def enforce_drift_gate(psi_by_feature: dict[str, float], maximum_psi: float) -> None:
    # TODO: raise ValueError if psi_by_feature is empty
    # TODO: collect every feature whose psi is AT or ABOVE maximum_psi
    # TODO: if any were collected, raise ValueError with a message that
    #       starts with "data drift detected:", shows ONLY the drifted
    #       features with their psi values, and states the threshold
    raise NotImplementedError
