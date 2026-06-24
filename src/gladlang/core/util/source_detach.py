"""Source detachment – recursively removes source text references from AST nodes to free memory."""


def detach_value(val):
    if isinstance(val, (list, tuple)):
        for item in val:
            detach_value(item)

    elif hasattr(val, "pos_start"):
        detach_source_from_node(val)


def detach_source_from_node(node, _visited=None):
    if node is None:
        return

    if _visited is None:
        _visited = {}

    node_id = id(node)
    if node_id in _visited and _visited[node_id] is node:
        return

    _visited[node_id] = node

    if hasattr(node, "pos_start") and node.pos_start:
        node.pos_start.detach_source()

    if hasattr(node, "pos_end") and node.pos_end:
        node.pos_end.detach_source()

    try:
        items = vars(node).items()
    except TypeError:
        items = []
        for name in dir(node):
            if name.startswith("__") or callable(getattr(node, name)):
                continue

            items.append((name, getattr(node, name)))

    for _, val in items:
        detach_value(val)
