import math

PSI_MINIMUM_PROPORTION = 1e-4


def compute_psi(
    expected_proportions: tuple[float, ...], actual_proportions: tuple[float, ...]
) -> float:
    if len(expected_proportions) != len(actual_proportions):
        raise ValueError(
            f"proportion vectors differ in length: "
            f"{len(expected_proportions)} vs {len(actual_proportions)}"
        )
    psi_total = 0.0
    for expected, actual in zip(expected_proportions, actual_proportions):
        clipped_expected = max(expected, PSI_MINIMUM_PROPORTION)
        clipped_actual = max(actual, PSI_MINIMUM_PROPORTION)
        psi_total += (clipped_actual - clipped_expected) * math.log(
            clipped_actual / clipped_expected
        )
    return round(psi_total, 4)
