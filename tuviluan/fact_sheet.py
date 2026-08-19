def build_fact_sheet(chart, engine_facts, validation, selected_year):
    return {
        "schema_version": "2.0",
        "selected_year": selected_year,
        "chart_input": chart,
        "engine_facts": engine_facts,
        "validation": validation,
        "confidence_policy": {
            "source_of_truth": "python_engine",
            "ocr_is_not_truth": True,
            "uncertain_items_are_not_facts": True,
        },
    }
