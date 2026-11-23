"""Keep pytest and its Python children away from live editorial inputs and runners."""

import ntpath
import os
import re
import sys

REPORT_ENV = "CONTENTOPS_TEST_ISOLATION_REPORT"
MAIN_EXPORT = r"a:\capital chronicle\researchruns\plan-status-v1"
MODEL_COMMANDS = {"agy", "agy.exe", "agy.cmd", "agy.ps1",
                  "codex", "codex.exe", "codex.cmd", "codex.ps1", "codex.js"}


class TestIsolationError(BaseException):
    """Escape production exception handlers that normally recover from I/O errors."""


def _is_main_export(path):
    if not isinstance(path, (str, bytes)):
        return False
    path = os.fsdecode(path)
    if "plan-status-v1" not in path.lower():
        return False
    if not ntpath.isabs(path):
        path = os.path.abspath(path)
    path = ntpath.normcase(ntpath.normpath(path)).removeprefix("\\\\?\\")
    return path == MAIN_EXPORT or path.startswith(MAIN_EXPORT + "\\")


def _command_parts(command):
    if isinstance(command, str):
        # Popen reports the Windows command line as a string and POSIX argv as a list.
        return [part.strip('"') for part in re.findall(r'"[^"]*"|[^\s"]+', command)]
    return [os.fsdecode(part) for part in command]


def install():
    def refuse(message):
        report_path = os.environ.get(REPORT_ENV)
        if report_path:
            with open(report_path, "a", encoding="utf-8") as report:
                report.write(message + "\n")
        raise TestIsolationError(message)

    def audit(event, arguments):
        if event in {"open", "os.listdir", "os.scandir", "os.chdir"}:
            if _is_main_export(arguments[0]):
                refuse("Live Main plan-status export reached. Supply a fixture export.")
        elif event == "subprocess.Popen":
            executable, command, cwd, _ = arguments
            parts = _command_parts(command)
            first = parts[0] if parts else ""
            names = {ntpath.basename(os.fsdecode(value)).lower() for value in (executable, first) if value}
            if names & MODEL_COMMANDS:
                refuse("Live Antigravity or Codex runner reached. Stub the model call.")
            if any(_is_main_export(path) for path in (cwd, *parts)):
                refuse("Live Main plan-status export reached. Supply a fixture export.")
            # A detached worker can outlive the test and its teardown. Test its
            # command with a fake Popen or run its draft phase with fixture inputs.
            if (len(parts) > 2 and ntpath.basename(parts[1]).lower() == "plan_analysis_pages.py"
                    and parts[2] == "draft-due"):
                refuse("Detached plan page worker reached. Stub the worker launch.")

    sys.addaudithook(audit)


if __name__ == "sitecustomize" and os.environ.get(REPORT_ENV):
    install()
