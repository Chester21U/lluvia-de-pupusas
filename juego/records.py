import json
from pathlib import Path

RUTA_RECORD = Path(__file__).resolve().parent.parent / "datos" / "record.json"


def cargar_record(ruta=RUTA_RECORD):
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return max(0, int(datos.get("record", 0)))
    except (OSError, json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return 0


def guardar_record(valor, ruta=RUTA_RECORD):
    ruta = Path(ruta)
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"record": int(valor)}), encoding="utf-8")
        return True
    except OSError:
        return False
