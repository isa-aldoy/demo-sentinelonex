def compute_score(results):
    # Simple scoring: count plugins with no error and return A-F
    total = len(results)
    passed = sum(1 for r in results.values() if not r.get("error"))
    if total == 0:
        return "N/A"
    percent = passed / total
    if percent == 1.0:
        return "A"
    elif percent >= 0.8:
        return "B"
    elif percent >= 0.6:
        return "C"
    elif percent >= 0.4:
        return "D"
    elif percent >= 0.2:
        return "E"
    else:
        return "F"
