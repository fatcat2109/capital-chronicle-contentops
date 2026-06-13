import ast
import re

files = [
    "live_contentops/scd_canonical_draft_lifecycle.py",
    "tests/test_scd_canonical_draft_lifecycle.py"
]

print("--- LINE COUNT AND EOF/TAIL READBACK ---")
for f in files:
    with open(f, "r", encoding="utf-8") as file:
        lines = file.readlines()
        print(f"{f}: {len(lines)} lines")
        print("Tail (last 2 lines):")
        for line in lines[-2:]:
            print(f"  {repr(line)}")

print("\n--- STATIC SCAN ---")
bad_patterns = re.compile(r"(provider|network|credential|env|API|browser|live)", re.IGNORECASE)
for f in files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
        matches = bad_patterns.findall(content)
        unique_matches = set(m.lower() for m in matches)
        print(f"{f} contains matches for: {unique_matches}")

print("\n--- REQUIRED SYMBOL CHECK ---")
expected_symbols = [
    "validate_canonical_draft_lifecycle_input",
    "validate_canonical_draft_attempt_ledger_entry",
    "validate_canonical_draft_validation_result",
    "validate_targeted_repair_patch_plan",
    "validate_canonical_draft_lifecycle_report",
    "build_attempt_ledger_entry",
    "build_lifecycle_report",
    "CANONICAL_DRAFT_LIFECYCLE_VALIDATORS"
]

for f in files:
    with open(f, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=f)
        names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))]
        names += [target.id for node in ast.walk(tree) if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)]
        
        if "scd_canonical_draft_lifecycle.py" in f:
            for s in expected_symbols:
                if s in names:
                    print(f"FOUND REQUIRED: {s}")
                else:
                    print(f"MISSING REQUIRED: {s}")

print("\n--- AST DUPLICATE SYMBOL SCAN ---")
for f in files:
    with open(f, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=f)
        names = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))]
        top_level_assigns = [target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)]
        all_symbols = names + top_level_assigns
        duplicates = set([x for x in all_symbols if all_symbols.count(x) > 1])
        print(f"{f} duplicates: {duplicates}")
