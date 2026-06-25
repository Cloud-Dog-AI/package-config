# cloud_dog_config Examples

## Load a config snapshot
```python
from cloud_dog_config import load_config

cfg = load_config(env_files=["tests/env-UT"])
```

## Read a nested value
```python
from cloud_dog_config import get_config

provider = get_config("llm.provider")
```
