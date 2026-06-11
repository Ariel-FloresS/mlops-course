def render_drift_report(
    psi_by_feature: dict[str, float],
    maximum_psi: float,
    reference_row_count: int,
    current_record_count: int,
) -> str:
    lines = [
        "DATA DRIFT REPORT",
        "=================",
        "",
        f"reference rows:   {reference_row_count}",
        f"current records:  {current_record_count}",
        f"psi threshold:    {maximum_psi}",
        "",
        f"  {'feature':<20} {'psi':<10} status",
    ]
    for feature_name, psi in psi_by_feature.items():
        status = "DRIFT" if psi >= maximum_psi else "ok"
        lines.append(f"  {feature_name:<20} {psi:<10} {status}")
    drifted_count = sum(1 for psi in psi_by_feature.values() if psi >= maximum_psi)
    lines.append("")
    lines.append(f"drifted features: {drifted_count} of {len(psi_by_feature)}")
    return "\n".join(lines) + "\n"
