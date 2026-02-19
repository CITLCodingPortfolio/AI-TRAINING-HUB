import os
import sys
import json
import shutil
import platform
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional
@dataclass
class GPUInfo:
    name: str
    vendor: str = "unknown"
    vram_total_mb: Optional[int] = None
    vram_used_mb: Optional[int] = None
    temp_c: Optional[int] = None
    util_pct: Optional[int] = None
    source: str = "unknown"
def _run(cmd: List[str], timeout: int = 3) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f"Command failed: {cmd}")
    return p.stdout.strip()
def _probe_nvidia_smi() -> List[GPUInfo]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    # Query: name,temp,util,mem_total,mem_used
    out = _run([exe, "--query-gpu=name,temperature.gpu,utilization.gpu,memory.total,memory.used",
                "--format=csv,noheader,nounits"], timeout=4)
    gpus: List[GPUInfo] = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        name = parts[0]
        temp = _to_int(parts[1])
        util = _to_int(parts[2])
        mem_total = _to_int(parts[3])
        mem_used = _to_int(parts[4])
        gpus.append(GPUInfo(
            name=name, vendor="nvidia",
            temp_c=temp, util_pct=util,
            vram_total_mb=mem_total, vram_used_mb=mem_used,
            source="nvidia-smi"
        ))
    return gpus
def _to_int(x: str) -> Optional[int]:
    try:
        return int(str(x).strip())
    except Exception:
        return None
def _probe_windows_wmic() -> List[GPUInfo]:
    if platform.system().lower() != "windows":
        return []
    # name + AdapterRAM only (no reliable temp here)
    try:
        out = _run(["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM", "/format:csv"], timeout=4)
    except Exception:
        return []
    gpus: List[GPUInfo] = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("Node,") or "," not in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        # Node,AdapterRAM,Name
        if len(parts) < 3:
            continue
        adapter_ram = _to_int(parts[1])
        name = parts[2] or "GPU"
        vram_mb = int(adapter_ram / (1024*1024)) if adapter_ram else None
        gpus.append(GPUInfo(
            name=name, vendor="windows",
            vram_total_mb=vram_mb,
            source="wmic"
        ))
    return gpus
def get_gpus() -> List[GPUInfo]:
    # Priority: nvidia-smi -> wmic (windows) -> empty
    gpus = _probe_nvidia_smi()
    if gpus:
        return gpus
    gpus = _probe_windows_wmic()
    if gpus:
        return gpus
    return []
def to_json() -> str:
    return json.dumps([asdict(g) for g in get_gpus()], indent=2)