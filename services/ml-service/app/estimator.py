PART_COSTS = {
    "tire": 6000, "headlight": 8000, "tail light": 6000, "fog light": 4000,
    "bumper": 10000, "door": 15000, "hood": 12000, "windshield": 11000,
    "dashboard": 20000, "console": 18000, "steering wheel": 15000,
}
DAMAGE_WEIGHT = {"glass shatter": 1.2, "dent": 1.0, "scratch": 0.6, "no damage": 0.0}
SEVERITY_MULTIPLIER = {"minor": 0.5, "moderate": 1.0, "severe": 1.8}
AIRBAG_SURCHARGE = 25000   # deployed airbag = major repair cost

def estimate_cost(result: dict) -> int:
    base = PART_COSTS.get(result["damaged_part"].lower(), 8000)
    dmg  = DAMAGE_WEIGHT.get(result["damage_type"].lower(), 1.0)
    sev  = SEVERITY_MULTIPLIER.get(result["severity"].lower(), 1.0)
    cost = base * dmg * sev
    if "deployed" in result["airbag_status"].lower():
        cost += AIRBAG_SURCHARGE
    return int(cost)
