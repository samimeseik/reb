import tempfile, pathlib
from reb.domain.ledger import Ledger
from reb.application.ingest import ingest_file
from reb.domain.errors import RebError
chat = "16.10.2026 09:15 - Ahmet Usta: siparis hazir\n16.10.2026 09:16 - Ali: tamam\n" * 5
for ext in [".txt", ".csv", ".md", ".log"]:
    d = pathlib.Path(tempfile.mkdtemp()); led = Ledger.init(d, name="t", subject="A", mode="engaged", authorization="m")
    p = d/("c"+ext); p.write_text(chat)
    try:
        r = ingest_file(led, p, custody="subject_held", origin_party="o"); print(ext, "ADMITTED kind=", r["source"]["kind"], "text has Ahmet:", "Ahmet" in (led.source_text(r["source"]["id"]) or ""))
    except RebError as e: print(ext, "blocked", e.code if hasattr(e,'code') else e)
