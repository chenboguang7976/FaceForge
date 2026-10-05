"""Build edition.

- ``pro``  — quality first: HyperSwap + pixel boost, occlusion masks, face
             restoration and high-quality encoding. Needs a strong machine.
- ``lite`` — tuned for low-end laptops (4-core CPU, 8 GB RAM, 4 GB GPU).

Both editions share all code and can reach every setting; the edition only
picks the defaults and the hardware warning. The build scripts overwrite
``EDITION`` below; ``FACEFORGE_EDITION`` overrides it at runtime.
"""
import os

EDITION = "pro"


def current() -> str:
    value = os.environ.get("FACEFORGE_EDITION", EDITION).strip().lower()
    return value if value in ("pro", "lite") else "pro"


def is_lite() -> bool:
    return current() == "lite"
