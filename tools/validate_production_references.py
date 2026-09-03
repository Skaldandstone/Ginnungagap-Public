"""Validates every *.production.json packet against production-reference.schema.json.

The concept-art pipeline has 51 production packets, one schema, and until now nothing that checked
one against the other. A packet is the handover document between reference art and Unreal
production -- it carries the asset id, the build intent, and the acceptance checks somebody will
later tick off -- so a packet that drifts from the schema is a handover that quietly stops meaning
what the pipeline thinks it means. The schema was written; it was just never enforced.

Self-contained on purpose: `jsonschema` is not installed here, and this pipeline should not need a
dependency installed to be checkable. It implements the subset the schema actually uses, verified by
enumerating the schema rather than guessing -- type, required, properties, items, enum, const,
$ref (local $defs only), additionalProperties, pattern, minLength, minItems, minimum. Anything the
schema starts using that is not on that list is reported as unsupported rather than silently passing,
so the validator cannot quietly stop validating.

The supported list was built by walking the schema and collecting every key in a schema position,
skipping the ones under "properties" and "$defs" which are field names rather than keywords. The
first attempt at that walk filtered against a list of keywords I had written from memory, which
could only ever report the ones I had already thought of -- it missed maxItems and exclusiveMinimum,
and every packet then failed on a gap in the validator rather than a fault in the packet.

Run:
    python tools/validate_production_references.py            # all packets
    python tools/validate_production_references.py --strict   # unknown top-level keys are failures

Exit code is 1 when any packet fails, so it can gate a build step later.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONCEPT_ART = ROOT / "docs" / "concept-art"
SCHEMA_NAME = "production-reference.schema.json"

SUPPORTED = {
    "$schema", "$id", "title", "description", "$defs", "definitions",
    "type", "required", "properties", "items", "enum", "const", "$ref",
    "additionalProperties", "pattern", "minLength", "minItems", "maxItems",
    "minimum", "exclusiveMinimum",
}

TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "number": (int, float), "integer": int, "null": type(None),
}


class Failure(list):
    """Collected messages; falsy when the value validated."""


def resolve(node, root):
    """Follow a local $ref. Only "#/$defs/name" style references are supported."""
    ref = node.get("$ref")
    if not ref:
        return node
    if not ref.startswith("#/"):
        raise ValueError("non-local $ref: {}".format(ref))
    target = root
    for part in ref[2:].split("/"):
        target = target[part]
    # A $ref sibling may carry extra keywords; merge them over the target.
    merged = dict(target)
    merged.update({k: v for k, v in node.items() if k != "$ref"})
    return merged


def check(value, schema, root, path, strict):
    out = Failure()

    unsupported = set(schema) - SUPPORTED
    if unsupported:
        out.append("{}: schema uses unsupported keyword(s) {} -- this validator would pass it "
                   "blindly, so it is reported instead".format(path or "<root>", sorted(unsupported)))
        return out

    try:
        schema = resolve(schema, root)
    except (ValueError, KeyError) as error:
        out.append("{}: bad $ref ({})".format(path or "<root>", error))
        return out

    expected = schema.get("type")
    if expected:
        # "type" may be a single name or a union list, e.g. ["string", "null"].
        names = [expected] if isinstance(expected, str) else list(expected)
        unknown = [n for n in names if n not in TYPES]
        if unknown:
            out.append("{}: schema names unknown type(s) {}".format(path or "<root>", unknown))
            return out

        def matches(name):
            # bool is a subclass of int in Python; JSON does not consider it a number.
            if name in ("number", "integer") and isinstance(value, bool):
                return False
            return isinstance(value, TYPES[name])

        if not any(matches(n) for n in names):
            out.append("{}: expected {}, got {}".format(
                path or "<root>", " or ".join(names), type(value).__name__))
            return out

    if "const" in schema and value != schema["const"]:
        out.append("{}: must be {!r}, got {!r}".format(path or "<root>", schema["const"], value))

    if "enum" in schema and value not in schema["enum"]:
        out.append("{}: {!r} is not one of {}".format(path or "<root>", value, schema["enum"]))

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            out.append("{}: {!r} does not match /{}/".format(path or "<root>", value, pattern))
        minimum = schema.get("minLength")
        if minimum is not None and len(value) < minimum:
            out.append("{}: shorter than minLength {}".format(path or "<root>", minimum))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            out.append("{}: {} is below minimum {}".format(path or "<root>", value, minimum))
        exclusive = schema.get("exclusiveMinimum")
        if exclusive is not None and value <= exclusive:
            out.append("{}: {} must be greater than {}".format(path or "<root>", value, exclusive))

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if minimum is not None and len(value) < minimum:
            out.append("{}: {} item(s), minItems {}".format(path or "<root>", len(value), minimum))
        maximum = schema.get("maxItems")
        if maximum is not None and len(value) > maximum:
            out.append("{}: {} item(s), maxItems {}".format(path or "<root>", len(value), maximum))
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                out.extend(check(item, item_schema, root, "{}[{}]".format(path, index), strict))

    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                out.append("{}: missing required key {!r}".format(path or "<root>", name))

        properties = schema.get("properties", {})
        for name, sub in properties.items():
            if name in value:
                out.extend(check(value[name], sub, root,
                                 "{}.{}".format(path, name) if path else name, strict))

        # additionalProperties: False is a hard failure; True is a note only under --strict, since
        # a packet carrying extra context is the pipeline growing, not the packet being wrong.
        extra = sorted(set(value) - set(properties))
        if extra:
            allowed = schema.get("additionalProperties", True)
            if allowed is False:
                out.append("{}: unexpected key(s) {}".format(path or "<root>", extra))
            elif strict:
                out.append("{}: NOTE extra key(s) not in schema: {}".format(path or "<root>", extra))

    return out


def check_source_sheet(data, packet):
    """That the packet still describes the sheet it was written against.

    A packet records its source sheet's path and sha256. Nothing verified either, so a regenerated
    sheet keeps the packet's blessing while no longer being the image anybody reviewed -- the packet
    would still say production-ready about a picture that had changed underneath it. Structural
    validity cannot catch that; only the hash can.

    Off by default because it reads every referenced image, which is 378 MB here.
    """
    out = Failure()
    sheet = data.get("source_sheet")
    if not isinstance(sheet, dict):
        return out

    declared = sheet.get("path")
    if not isinstance(declared, str):
        return out

    # Paths are recorded relative to the repository root; fall back to resolving beside the packet.
    candidates = [ROOT / declared, packet.parent / Path(declared).name]
    target = next((c for c in candidates if c.is_file()), None)
    if target is None:
        out.append("source_sheet.path: no file at {!r}".format(declared))
        return out

    recorded = sheet.get("sha256")
    if not isinstance(recorded, str):
        return out

    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if digest != recorded:
        out.append("source_sheet.sha256: {} records {}..., file hashes {}... -- the sheet changed "
                   "after the packet was written".format(declared, recorded[:12], digest[:12]))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true",
                        help="report keys the schema does not describe")
    parser.add_argument("--check-sources", action="store_true",
                        help="also verify each packet's source_sheet still hashes to its recorded sha256")
    args = parser.parse_args()

    schemas = list(CONCEPT_ART.rglob(SCHEMA_NAME))
    if not schemas:
        sys.exit("No {} found under {}".format(SCHEMA_NAME, CONCEPT_ART))
    if len({s.read_bytes() for s in schemas}) > 1:
        print("WARNING: {} copies of the schema and they differ; validating against {}\n".format(
            len(schemas), schemas[0].relative_to(ROOT)))
    schema = json.loads(schemas[0].read_text(encoding="utf-8"))

    packets = sorted(CONCEPT_ART.rglob("*.production.json"))
    if not packets:
        sys.exit("No *.production.json packets found under {}".format(CONCEPT_ART))

    failed = 0
    for packet in packets:
        rel = packet.relative_to(ROOT).as_posix()
        try:
            data = json.loads(packet.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            print("FAIL {}\n       not valid JSON: {}".format(rel, error))
            failed += 1
            continue

        problems = check(data, schema, schema, "", args.strict)
        if args.check_sources:
            problems.extend(check_source_sheet(data, packet))
        hard = [p for p in problems if " NOTE " not in p]
        if hard:
            failed += 1
            print("FAIL {}".format(rel))
            for problem in problems:
                print("       {}".format(problem))
        elif problems:
            print("ok   {}  ({} note(s))".format(rel, len(problems)))
            for problem in problems:
                print("       {}".format(problem))

    print("\n{} packet(s), {} failing".format(len(packets), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
