def convert(value: str, into: str = "float"):
    if "float" == into:
        try:
            value = float(value.replace(",", "."))
        finally:
            return value
