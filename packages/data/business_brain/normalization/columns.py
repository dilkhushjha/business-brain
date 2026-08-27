def normalize_column_name(name: str) -> str:
    return "_".join(name.strip().lower().replace("-", " ").split())
