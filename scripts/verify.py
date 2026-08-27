"""Validaciones locales reproducibles para FinanceOS.

Niveles:
  commit: comprobaciones rápidas sobre lo preparado en Git.
  push: pruebas de backend y compilaciones de web/móvil.
  full: push más auditorías de dependencias.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {"__pycache__", ".venv", "node_modules", ".dart_tool", "uploads", "backups"}
FORBIDDEN_NAMES = {".env", "finance.db", "correo-desarrollo.txt", ".mfa_key"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite3", ".apk", ".aab", ".ipa"}
SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(?:OPENAI|CODEX)_(?:API_)?KEY\b\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+[a-z0-9._~-]{16,}"),
)


def run(command: list[str], cwd: Path = ROOT, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print(f"\n> {' '.join(command)}")
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=capture,
    )


def git_lines(*args: str) -> list[str]:
    result = run(["git", *args], capture=True)
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def staged_files() -> list[str]:
    return git_lines("diff", "--cached", "--name-only", "--diff-filter=ACMR")


def changed_for_push() -> list[str]:
    upstream = run(["git", "rev-parse", "--abbrev-ref", "@{upstream}"], capture=True)
    if upstream.returncode == 0:
        base = upstream.stdout.strip()
        return git_lines("diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD")
    return git_lines("diff", "--name-only", "--diff-filter=ACMR", "HEAD~1", "HEAD")


def is_forbidden(path_text: str) -> bool:
    path = Path(path_text)
    return (
        bool(FORBIDDEN_PARTS.intersection(path.parts))
        or path.name in FORBIDDEN_NAMES
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
    )


def check_staged_files(files: list[str]) -> None:
    forbidden = [path for path in files if is_forbidden(path)]
    if forbidden:
        print("\nERROR: estos archivos locales o sensibles no deben entrar al commit:")
        for path in forbidden:
            print(f"  - {path}")
        print("Retíralos con: git restore --staged <archivo>")
        raise SystemExit(1)


def check_staged_secrets() -> None:
    result = run(["git", "diff", "--cached", "--unified=0", "--no-color"], capture=True)
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    findings: list[str] = []
    current_file = "archivo desconocido"
    for line in result.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            findings.append(current_file)

    if findings:
        print("\nERROR: posible secreto detectado en cambios preparados:")
        for path in sorted(set(findings)):
            print(f"  - {path}")
        print("Revisa el diff y usa variables de entorno o un gestor de secretos.")
        raise SystemExit(1)


def compile_changed_python(files: list[str]) -> None:
    python_files = [path for path in files if path.endswith(".py") and (ROOT / path).is_file()]
    if not python_files:
        print("OK: no hay archivos Python preparados.")
        return
    result = run([sys.executable, "-m", "py_compile", *python_files])
    if result.returncode:
        raise SystemExit(result.returncode)


def flutter_command() -> str | None:
    configured = os.getenv("FLUTTER_BIN")
    candidates = [
        configured,
        shutil.which("flutter"),
        str(Path.home() / ".puro" / "envs" / "stable" / "flutter" / "bin" / "flutter.bat"),
    ]
    return next((item for item in candidates if item and Path(item).exists()), None)


def require_success(command: list[str], cwd: Path = ROOT) -> None:
    result = run(command, cwd)
    if result.returncode:
        raise SystemExit(result.returncode)


def verify_commit() -> None:
    files = staged_files()
    if not files:
        print("No hay cambios preparados. Usa git add antes de crear el commit.")
        raise SystemExit(1)
    check_staged_files(files)
    check_staged_secrets()
    compile_changed_python(files)
    print("\nOK: validación rápida del commit completada.")


def verify_push() -> None:
    files = changed_for_push()
    force_all = any(path.startswith(("scripts/", ".githooks/", ".github/")) for path in files)
    backend_changed = force_all or any(
        path.endswith(".py") or path.startswith(("api/", "core/", "tests/", "requirements"))
        for path in files
    )
    frontend_changed = force_all or any(path.startswith("frontend/") for path in files)
    mobile_changed = force_all or any(path.startswith("mobile/") for path in files)

    if backend_changed:
        require_success([
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--basetemp=.pytest-tmp",
        ])
    else:
        print("OK: backend sin cambios; pruebas omitidas.")

    if frontend_changed:
        npm = shutil.which("npm")
        if npm is None:
            raise SystemExit("ERROR: npm no está disponible; no se pudo validar el frontend.")
        require_success([npm, "run", "build"], ROOT / "frontend")
    else:
        print("OK: frontend sin cambios; compilación omitida.")

    if mobile_changed:
        flutter = flutter_command()
        if flutter is None:
            raise SystemExit("ERROR: Flutter no está disponible. Configura FLUTTER_BIN o instala Flutter.")
        require_success([flutter, "analyze"], ROOT / "mobile")
        require_success([flutter, "test"], ROOT / "mobile")
    else:
        print("OK: móvil sin cambios; validación omitida.")
    print("\nOK: las áreas modificadas están validadas para subir.")


def verify_full() -> None:
    require_success([
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--basetemp=.pytest-tmp",
    ])
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("ERROR: npm no está disponible; no se pudo validar el frontend.")
    require_success([npm, "run", "build"], ROOT / "frontend")
    flutter = flutter_command()
    if flutter is None:
        raise SystemExit("ERROR: Flutter no está disponible. Configura FLUTTER_BIN o instala Flutter.")
    require_success([flutter, "analyze"], ROOT / "mobile")
    require_success([flutter, "test"], ROOT / "mobile")
    require_success([sys.executable, "-m", "pip_audit", "-r", "requirements.txt"])
    require_success([npm, "audit", "--omit=dev", "--audit-level=high"], ROOT / "frontend")
    print("\nOK: validación integral y auditorías completadas.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida FinanceOS antes de commit, push o publicación.")
    parser.add_argument("level", choices=("commit", "push", "full"))
    args = parser.parse_args()
    {"commit": verify_commit, "push": verify_push, "full": verify_full}[args.level]()


if __name__ == "__main__":
    main()
