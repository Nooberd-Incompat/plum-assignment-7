def analyze_trends(current_tests: list, previous_tests: list) -> list:
    """
    Compares current test results with previous ones to identify trends.
    """
    # Create a quick lookup dictionary for previous tests
    previous_tests_map = {test.name.lower(): test for test in previous_tests}

    for current_test in current_tests:
        test_name_lower = current_test.get("name", "").lower()
        previous_test = previous_tests_map.get(test_name_lower)

        if previous_test:
            current_value = float(current_test.get("value", 0))
            previous_value = float(previous_test.value)

            # Add previous value for context
            current_test["previous_value"] = previous_value

            # Determine the trend
            if current_value > previous_value:
                current_test["trend"] = "increasing"
            elif current_value < previous_value:
                current_test["trend"] = "decreasing"
            else:
                current_test["trend"] = "stable"
    
    return current_tests