#!/usr/bin/env python3
"""
Environment Verification Script
Checks system prerequisites, Python runtime, Java/Spark availability, core packages,
hardware specs, directory write permissions, and storage capacity.
"""

import sys
import os
import shutil
import platform
import subprocess
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def status_tag(status: str) -> str:
    if status == "PASS":
        return f"[{GREEN}PASS{RESET}]"
    elif status == "WARN":
        return f"[{YELLOW}WARN{RESET}]"
    elif status == "FAIL":
        return f"[{RED}FAIL{RESET}]"
    elif status == "OPTIONAL":
        return f"[{BLUE}OPTIONAL{RESET}]"
    elif status == "NOT INSTALLED":
        return f"[{YELLOW}NOT INSTALLED{RESET}]"
    return f"[{status}]"

def check_python() -> tuple[bool, str]:
    ver = sys.version_info
    ver_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    if ver.major == 3 and ver.minor in (10, 11):
        return True, f"Python {ver_str} (Target 3.10/3.11 satisfied)"
    elif ver.major == 3 and ver.minor >= 12:
        return True, f"Python {ver_str} (Warning: PySpark/PyTorch compatibility is best on 3.10/3.11)"
    return False, f"Python {ver_str} (Unsupported. Requires Python 3.10 or 3.11)"

def check_virtualenv() -> tuple[bool, str]:
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        return True, f"Active virtualenv at {sys.prefix}"
    return False, "Not running inside a virtual environment. (Create and activate .venv)"

def check_command(cmd: str, min_ver_arg: str = "--version") -> tuple[bool, str]:
    path = shutil.which(cmd)
    if not path:
        return False, f"Command '{cmd}' not found on PATH"
    try:
        res = subprocess.run([cmd, min_ver_arg], capture_output=True, text=True, timeout=5)
        out = (res.stdout or res.stderr).strip().split("\n")[0]
        return True, f"{cmd} available ({out})"
    except Exception as e:
        return True, f"{cmd} found at {path} (version check failed: {e})"

def check_java() -> tuple[str, str]:
    java_path = shutil.which("java")
    java_home = os.environ.get("JAVA_HOME", "")
    if not java_path:
        return "WARN", "Java not found on PATH. (Required for PySpark batch jobs in Phase 4)"
    try:
        res = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
        out = (res.stderr or res.stdout).strip().split("\n")[0]
        msg = f"Java runtime available: {out}"
        if java_home:
            msg += f" (JAVA_HOME={java_home})"
        return "PASS", msg
    except Exception as e:
        return "WARN", f"Java execution error: {e}"

def check_package(module_name: str, import_name: str | None = None) -> tuple[str, str]:
    import_target = import_name or module_name
    try:
        mod = __import__(import_target)
        version = getattr(mod, "__version__", "installed")
        return "PASS", f"{module_name} {version}"
    except ImportError:
        return "FAIL", f"{module_name} is missing (run: pip install -r requirements/dev.txt)"

def check_optional_package(module_name: str, phase_name: str) -> tuple[str, str]:
    try:
        mod = __import__(module_name)
        version = getattr(mod, "__version__", "installed")
        return "PASS", f"{module_name} {version} (Ready for {phase_name})"
    except ImportError:
        return "OPTIONAL", f"{module_name} (Scheduled for {phase_name}; not installed yet)"

def check_disk_space(project_root: Path) -> tuple[bool, str]:
    try:
        usage = shutil.disk_usage(project_root)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        if free_gb >= 5.0:
            return True, f"{free_gb:.1f} GB free of {total_gb:.1f} GB disk space (Sufficient)"
        elif free_gb >= 2.0:
            return True, f"{free_gb:.1f} GB free (Warning: Low disk space, recommend >5 GB)"
        else:
            return False, f"{free_gb:.1f} GB free (Insufficient disk space; <2 GB available)"
    except Exception as e:
        return True, f"Disk check skipped ({e})"

def check_directory_permissions(project_root: Path) -> list[tuple[str, str, str]]:
    dirs_to_check = [
        "data/raw",
        "data/processed",
        "data/evaluation",
        "data/telemetry",
        "data/vector_store",
        "logs",
    ]
    results = []
    for rel_dir in dirs_to_check:
        p = project_root / rel_dir
        p.mkdir(parents=True, exist_ok=True)
        test_file = p / ".perm_check"
        try:
            test_file.write_text("ok")
            test_file.unlink()
            results.append(("PASS", rel_dir, f"Directory exists and is writable ({p})"))
        except Exception as e:
            results.append(("FAIL", rel_dir, f"Cannot write to {rel_dir}: {e}"))
    return results

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    print("=" * 70)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — ENVIRONMENT VERIFICATION")
    print("=" * 70)
    print(f"Project Root Directory : {project_root}")
    print(f"Operating System       : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python Executable      : {sys.executable}")
    print("-" * 70)

    critical_failures = 0
    warnings = 0

    # 1. System & Runtime Checks
    print("\n[1] SYSTEM & RUNTIME PREREQUISITES")
    py_ok, py_msg = check_python()
    print(f"  {status_tag('PASS' if py_ok else 'FAIL')} {py_msg}")
    if not py_ok:
        critical_failures += 1

    venv_ok, venv_msg = check_virtualenv()
    print(f"  {status_tag('PASS' if venv_ok else 'FAIL')} {venv_msg}")
    if not venv_ok:
        critical_failures += 1

    git_ok, git_msg = check_command("git", "--version")
    print(f"  {status_tag('PASS' if git_ok else 'WARN')} {git_msg}")
    if not git_ok:
        warnings += 1

    java_status, java_msg = check_java()
    print(f"  {status_tag(java_status)} {java_msg}")
    if java_status == "WARN":
        warnings += 1

    disk_ok, disk_msg = check_disk_space(project_root)
    print(f"  {status_tag('PASS' if disk_ok else 'FAIL')} {disk_msg}")
    if not disk_ok:
        critical_failures += 1

    # 2. Hardware Architecture & Acceleration
    print("\n[2] HARDWARE SPECS & COMPUTE ACCELERATION")
    print(f"  {status_tag('PASS')} CPU Architecture: {platform.machine()} ({platform.processor() or 'Standard Multi-Core'})")
    
    # Check PyTorch / CUDA if installed
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        mps_avail = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        accel_desc = "CPU"
        if cuda_avail:
            accel_desc = f"CUDA GPU ({torch.cuda.get_device_name(0)})"
        elif mps_avail:
            accel_desc = "Apple Silicon MPS (Metal Performance Shaders)"
        print(f"  {status_tag('PASS')} PyTorch Acceleration: {accel_desc}")
    except ImportError:
        print(f"  {status_tag('OPTIONAL')} PyTorch not installed yet (CPU execution is default for Phase 2)")

    # 3. Core Framework & Database Dependencies
    print("\n[3] CORE APPLICATION & DATABASE PACKAGES (PHASE 1 BASELINE)")
    core_packages = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Pydantic", "pydantic"),
        ("Pydantic-Settings", "pydantic_settings"),
        ("SQLAlchemy", "sqlalchemy"),
        ("aiosqlite", "aiosqlite"),
        ("PyMuPDF (fitz)", "fitz"),
        ("python-docx", "docx"),
        ("pytest", "pytest"),
        ("httpx", "httpx"),
    ]
    for pkg_name, mod_name in core_packages:
        status, msg = check_package(pkg_name, mod_name)
        print(f"  {status_tag(status)} {msg}")
        if status == "FAIL":
            critical_failures += 1

    # 4. Optional / Future Dependencies (Phase 2, 3, 4)
    print("\n[4] FUTURE SUBSYSTEM DEPENDENCIES (PLANNED ROLLOUT)")
    future_packages = [
        ("torch", "Phase 2 (Embeddings)"),
        ("transformers", "Phase 2 (Embeddings)"),
        ("sentence_transformers", "Phase 2 (Embeddings)"),
        ("chromadb", "Phase 2 (Vector Store)"),
        ("google.genai", "Phase 3 (Hosted LLM)"),
        ("pyspark", "Phase 4 (Big Data Analytics)"),
    ]
    for mod_name, phase_desc in future_packages:
        status, msg = check_optional_package(mod_name, phase_desc)
        print(f"  {status_tag(status)} {msg}")

    # 5. Project Writable Directories
    print("\n[5] PROJECT STORAGE & DIRECTORY PERMISSIONS")
    dir_results = check_directory_permissions(project_root)
    for status, dir_name, msg in dir_results:
        print(f"  {status_tag(status)} {msg}")
        if status == "FAIL":
            critical_failures += 1

    print("\n" + "=" * 70)
    if critical_failures == 0:
        print(f"{GREEN}VERIFICATION PASSED:{RESET} Environment is ready for Phase 1 execution.")
        if warnings > 0:
            print(f"{YELLOW}Note:{RESET} {warnings} non-critical warning(s) observed.")
        print("=" * 70)
        return 0
    else:
        print(f"{RED}VERIFICATION FAILED:{RESET} {critical_failures} critical check(s) failed.")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
