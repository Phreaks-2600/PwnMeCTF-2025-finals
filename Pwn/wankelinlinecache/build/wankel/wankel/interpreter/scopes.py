from ..pyjsparser import std_nodes as ast_nodes

class Scope:
    def __init__(self, parent: 'Scope | None' = None):
        self.parent: Scope = parent
        self.registers: dict[str, int] = {}
        self.kinds: dict[str, str] = {}
        self.last_register_index = parent.last_register_index if parent else 0

        self.reserved_keywords = (
                'undefined',
                'null',
                'true',
                'false',
                'NaN',
            )


    def get_register(self, id: ast_nodes.BaseNode, recurse: bool = True,
                     create_with_kind_if_missing: str | None = None):
        assert id.type == ast_nodes.Syntax.Identifier

        if id.name in self.reserved_keywords:
            return None, None, None

        reg = self.registers.get(id.name)
        kind = self.kinds.get(id.name)
        created = False

        if reg is None and recurse and self.parent:
            reg, created, kind = self.parent.get_register(id, recurse)
            assert created == False

        if reg is None and create_with_kind_if_missing:
            created = True
            kind = create_with_kind_if_missing
            reg = self.last_register_index

            self.registers[id.name] = reg
            self.kinds[id.name] = kind
            self.last_register_index += 1


        return reg, created, kind


    def get_tmp_register(self):
        self.last_register_index += 1
        return self.last_register_index-1


    def shrink_to(self, new_last_index):
        self.last_register_index = new_last_index

        for x, y in self.registers.items():
            if y >= self.last_register_index:
                del self.registers[x]

