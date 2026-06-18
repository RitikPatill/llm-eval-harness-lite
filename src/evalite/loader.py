from pathlib import Path

import yaml
from pydantic import ValidationError

from evalite.schema import EvalSuite


def load_suite(path: str | Path) -> EvalSuite:
    path = Path(path)
    with path.open() as f:
        raw = yaml.safe_load(f)
    try:
        return EvalSuite.model_validate(raw)
    except ValidationError as e:
        raise ValueError(str(e)) from e
