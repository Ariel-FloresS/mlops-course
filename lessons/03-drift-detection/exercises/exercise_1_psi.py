import math

PSI_MINIMUM_PROPORTION = 1e-4


def compute_psi(
    expected_proportions: tuple[float, ...], actual_proportions: tuple[float, ...]
) -> float:
    # TODO: raise ValueError containing "differ in length" when the two
    #       vectors have different lengths
    # TODO: for every (expected, actual) pair:
    #       1. clip both to at least PSI_MINIMUM_PROPORTION
    #          (log(0) and division by zero must be impossible)
    #       2. accumulate (actual - expected) * ln(actual / expected)
    # TODO: return the total rounded to 4 decimals
    # NOTE: identical vectors must score exactly 0.0
    raise NotImplementedError
