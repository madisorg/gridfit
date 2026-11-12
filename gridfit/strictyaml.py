"""YAML loading that refuses a mapping key written twice.

PyYAML keeps the last of two equal keys without a word; the site's JS parser refuses the file. A brand file created on
two branches and joined by a merge (anker, enphase, invt and sigenergy, 2026-11-12) therefore built a site without the
first branch's documents in every Python step, and only `npm test` noticed. Every YAML read in tools/ and gridfit/
goes through `load`, so a doubled key stops the run instead of losing data."""
import yaml


class _Strict(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    seen = {}
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found duplicate key {key!r} (first on line {seen[key]})", key_node.start_mark)
        seen[key] = key_node.start_mark.line + 1
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_Strict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load(text):
    """yaml.safe_load, except that a key written twice in one mapping is an error."""
    return yaml.load(text, Loader=_Strict)
