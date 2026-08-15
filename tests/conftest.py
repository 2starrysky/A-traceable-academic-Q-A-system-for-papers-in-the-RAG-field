"""pytest 共享配置:把项目根加入 sys.path,使 src 可直接 import。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
