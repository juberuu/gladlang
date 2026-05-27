"""Final constant detection – checks if a name is a constant anywhere in the symbol table chain."""


def is_final_anywhere(table, name):
    while table:
        if table._finals_count == 0:
            table = table.parent
            continue

        with table._lock:
            if name in table.finals:
                return True
        table = table.parent

    return False
