def build_dc(domain: str) -> str:
    """
    Преобразует domain вида testdomain.local
    в DN: DC=testdomain,DC=local
    """
    parts = domain.split(".")
    return ",".join(f"DC={p}" for p in parts)
