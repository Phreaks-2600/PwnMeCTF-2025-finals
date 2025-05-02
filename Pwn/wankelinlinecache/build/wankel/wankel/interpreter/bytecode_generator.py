from . import bytecode_array
from ..objects import function as fn, jsvalue
from .. import globals
from .. import runtime

from . import scopes

from .. import exceptions

from ..pyjsparser import std_nodes as ast_nodes

import ctypes


def accepted_node_types(node_types: list[ast_nodes.Syntax]):
    def decorator(f):
        def wrapper(self, node: ast_nodes.BaseNode, *args, **kwargs):
            if node.type not in node_types:
                raise exceptions.UnsupportedException(f"Unsupported node type: `{node.type}`")
            return f(self, node, *args, **kwargs)
        return wrapper
    return decorator

class BytecodeGenerator:
    def __init__(self, print_bytecode_flag):
        self.print_bytecode_flag = print_bytecode_flag

        self.current_scope: scopes.Scope | None = None
        self.bytecode_arrays: list[bytecode_array.BytecodeArray] = []



    def push_scope(self):
        self.current_scope = scopes.Scope(self.current_scope)

    def pop_scope(self):
        self.current_scope = self.current_scope.parent


    @property
    def current_bytecode_array(self):
        return self.bytecode_arrays[-1]

    def push_bytecode_array(self):
        self.bytecode_arrays.append(bytecode_array.BytecodeArray())

    def pop_bytecode_array(self):
        # Add a `return undefined` here, in case there is no return before it
        self.current_bytecode_array.ldaundefined()
        self.current_bytecode_array.ret()

        bc_arr = self.bytecode_arrays.pop()
        bc_arr_alloc = globals.BROKER.alloc_bytecode_array(bc_arr)

        if self.print_bytecode_flag:
            print(bc_arr_alloc)
            print()
            print()

        return ctypes.pointer(bc_arr_alloc)


    @property
    def constant_array(self):
        return self.current_bytecode_array.constant_array


    @accepted_node_types([
            ast_nodes.Syntax.BlockStatement,
            ast_nodes.Syntax.VariableDeclaration,
            ast_nodes.Syntax.EmptyStatement,
            ast_nodes.Syntax.ExpressionStatement,
            ast_nodes.Syntax.FunctionDeclaration,
            ast_nodes.Syntax.ReturnStatement,
            ast_nodes.Syntax.IfStatement,
            ast_nodes.Syntax.ForStatement,
        ])
    def visit_Statement(self, node: ast_nodes.BaseNode):
        match node.type:
            case ast_nodes.Syntax.BlockStatement:
                self.visit_BlockStatement(node)
            case ast_nodes.Syntax.VariableDeclaration:
                self.visit_VariableDeclaration(node)
            case ast_nodes.Syntax.EmptyStatement:
                pass
            case ast_nodes.Syntax.ExpressionStatement:
                last_register_before = self.current_scope.last_register_index
                self.visit_Expression(node.expression)
                self.current_scope.shrink_to(last_register_before)
            case ast_nodes.Syntax.FunctionDeclaration:
                self.visit_FunctionDeclaration(node)
            case ast_nodes.Syntax.ReturnStatement:
                self.visit_ReturnStatement(node)
            case ast_nodes.Syntax.IfStatement:
                self.visit_IfStatement(node)
            case ast_nodes.Syntax.ForStatement:
                self.visit_ForStatement(node)
            case _:
                raise exceptions.UnsupportedException("Unsupported node type while walking the AST")


    @accepted_node_types([ ast_nodes.Syntax.ReturnStatement ])
    def visit_ReturnStatement(self, node: ast_nodes.BaseNode):
        if node.argument:
            self.visit_Expression(node.argument)
        else:
            self.current_bytecode_array.ldaundefined()
        self.current_bytecode_array.ret()


    @accepted_node_types([
        ast_nodes.Syntax.FunctionDeclaration,
        ast_nodes.Syntax.FunctionExpression,
    ])
    def visit_FunctionDeclaration(self, node: ast_nodes.BaseNode):
        self.visit_FunctionExpression(node)

        f_reg, created, kind = self.current_scope.get_register(node.id, False, 'var')
        self.current_bytecode_array.star(f_reg)


    @accepted_node_types([
        ast_nodes.Syntax.FunctionDeclaration,
        ast_nodes.Syntax.FunctionExpression,
    ])
    def visit_FunctionExpression(self, node: ast_nodes.BaseNode):
        if node.generator:
            raise exceptions.UnsupportedException("Generators are not supported")
        assert node.expression == False # It looks like it's always true

        arity = len(node.params)

        self.push_bytecode_array()

        # TODO: Functions should be able to access outer scope
        outer_scope = self.current_scope
        self.current_scope = scopes.Scope(scopes.Scope()) # NOTE: We create an empty parent
                                            #       scope, so that we don't
                                            #       suppose that we use the
                                            #       `global` scope while
                                            #       creating new vars

        # Allocate slots for the arguments
        for param in node.params:
            self.current_scope.get_register(param, False, 'param')

        # Check for defaults
        for param, default in zip(node.params, node.defaults):
            if default is None:
                continue

            reg, created, kind = self.current_scope.get_register(param)

            assert created == False
            assert kind == 'param'

            undef_reg = self.current_scope.get_tmp_register()
            self.current_bytecode_array.ldaundefined()
            self.current_bytecode_array.star(undef_reg)

            self.current_bytecode_array.strictneq(reg, undef_reg)

            branch_bc_index = len(self.current_bytecode_array._bytecode_array)
            branch = self.current_bytecode_array.jmpif(0)

            self.visit_Expression(default)
            self.current_bytecode_array.star(reg)

            # Compute branch offset
            # TODO: Implement labels to make this logic easier
            offset = 0
            for bc in self.current_bytecode_array._bytecode_array[
                    branch_bc_index:]:
                offset += ctypes.sizeof(bc)

            branch.dest_offset = offset


        self.visit_BlockStatement(node.body)

        self.current_scope = outer_scope

        bc_arr_ptr = self.pop_bytecode_array()


        function = globals.BROKER.alloc(fn.JSFunction)
        function.map = globals.BROKER.builtin_maps[fn.JSFunction]
        function.entry = runtime.InterpreterTrampoline.__impl__
        function.arity = arity
        function.bytecode = bc_arr_ptr
        function.exec_type = 0                   # 0 means interpreted
        function.total_time = 0
        function.name = globals.BROKER.alloc_literal(node.id.name if node.id else
                                                  '', 'String')

        constant_id = self.constant_array.get_constant_id(jsvalue.TaggedPointer(
            ctypes.addressof(function)))
        self.current_bytecode_array.ldaconstant(constant_id)


    @accepted_node_types([
            ast_nodes.Syntax.Literal,
            ast_nodes.Syntax.Identifier,
            ast_nodes.Syntax.CallExpression,
            ast_nodes.Syntax.MemberExpression,
            ast_nodes.Syntax.ObjectExpression,
            ast_nodes.Syntax.ArrayExpression,
            ast_nodes.Syntax.AssignmentExpression,
            ast_nodes.Syntax.FunctionExpression,
            ast_nodes.Syntax.UnaryExpression,
            ast_nodes.Syntax.UpdateExpression,
            ast_nodes.Syntax.BinaryExpression,
            ast_nodes.Syntax.LogicalExpression,
            ast_nodes.Syntax.ConditionalExpression,
        ])
    def visit_Expression(self, node: ast_nodes.BaseNode):
        match node.type:
            case ast_nodes.Syntax.Literal:
                receiver = self.visit_Literal(node)
            case ast_nodes.Syntax.Identifier:
                receiver = self.visit_Identifier(node)
            case ast_nodes.Syntax.CallExpression:
                receiver = self.visit_CallExpression(node)
            case ast_nodes.Syntax.MemberExpression:
                receiver = self.visit_MemberExpression(node)
            case ast_nodes.Syntax.ObjectExpression:
                receiver = self.visit_ObjectExpression(node)
            case ast_nodes.Syntax.ArrayExpression:
                receiver = self.visit_ArrayExpression(node)
            case ast_nodes.Syntax.AssignmentExpression:
                receiver = self.visit_AssignmentExpression(node)
            case ast_nodes.Syntax.FunctionExpression:
                receiver = self.visit_FunctionExpression(node)
            case ast_nodes.Syntax.UnaryExpression:
                receiver = self.visit_UnaryExpression(node)
            case ast_nodes.Syntax.UpdateExpression:
                receiver = self.visit_UpdateExpression(node)
            case ast_nodes.Syntax.BinaryExpression:
                receiver = self.visit_BinaryExpression(node)
            case ast_nodes.Syntax.LogicalExpression:
                receiver = self.visit_LogicalExpression(node)
            case ast_nodes.Syntax.ConditionalExpression:
                receiver = self.visit_ConditionalExpression(node)
            case _:
                raise exceptions.UnsupportedException("Unsupported node type while walking the AST")

        return receiver


    @accepted_node_types([ ast_nodes.Syntax.Literal ])
    def visit_Literal(self, node: ast_nodes.BaseNode):
        value = node.value
        literal_type =                                                         \
                'Null' if node.raw == 'null' else                              \
                'String' if isinstance(value, str) else                        \
                'Boolean' if isinstance(value, bool) else                      \
                'SMI' if isinstance(value, int) or value.is_integer() and (
                        jsvalue.SMI(int(value)).value == int(value) and \
                        int(value) # Avoid storing zeros as SMI to keep the sign
                    ) else 'Number'


        if literal_type == 'SMI':
            self.current_bytecode_array.ldasmi(int(value))

        elif literal_type == 'Null':
            self.current_bytecode_array.ldanull()

        else:
            constant = globals.BROKER.alloc_literal(node.value, literal_type)
            constant_id = self.constant_array.get_constant_id(constant)
            self.current_bytecode_array.ldaconstant(constant_id)


    @accepted_node_types([ ast_nodes.Syntax.Identifier ])
    def visit_Identifier(self, node: ast_nodes.BaseNode):
        match node.name:
            case 'undefined':
                self.current_bytecode_array.ldaundefined()
            case 'NaN':
                constant_id = self.constant_array.get_constant_id(globals.BROKER.nan_number)
                self.current_bytecode_array.ldaconstant(constant_id)
            case _:
                reg, created, kind = self.current_scope.get_register(node)
                if reg is not None:
                    self.current_bytecode_array.ldar(reg)
                else:
                    constant_id = self.constant_array.get_constant_id(
                            globals.BROKER.alloc_literal(node.name, 'String')
                        )
                    self.current_bytecode_array.ldaglobal(constant_id)



    @accepted_node_types([ ast_nodes.Syntax.AssignmentExpression ])
    def visit_AssignmentExpression(self, node: ast_nodes.BaseNode):
        # TODO: Support other operators (`+=`, `-=`, etc.)
        assert node.operator in [
                '=',
                '&&=', '||=',
                '*=', '/=', '%=',
                '+=', '-=',
                '<<=', '>>=', '>>>=',
                '&=', '^=', '|=',
            ]

        assert node.left.type in [
                ast_nodes.Syntax.MemberExpression,
                ast_nodes.Syntax.Identifier
            ]

        if node.left.type is ast_nodes.Syntax.MemberExpression:
            self.visit_Expression(node.left.object)

            receiver = self.current_scope.get_tmp_register()
            self.current_bytecode_array.star(receiver)

            if node.left.computed:
                key_reg = self.current_scope.get_tmp_register()
                self.visit_Expression(node.left.property)
                self.current_bytecode_array.star(key_reg)
            else:
                constant_id = self.constant_array.get_constant_id(
                        globals.BROKER.alloc_literal(node.left.property.name, 'String')
                    )

            if node.operator != '=':
                left_reg = self.current_scope.get_tmp_register()
                if node.left.computed:
                    self.current_bytecode_array.getkeyedproperty(receiver)
                else:
                    self.current_bytecode_array.getnamedproperty(receiver,
                                                                 constant_id)
                self.current_bytecode_array.star(left_reg)

            self.visit_Expression(node.right)

            if node.operator != '=':
                right_reg = self.current_scope.get_tmp_register()
                self.current_bytecode_array.star(right_reg)

                match node.operator:
                    case '&&=':
                        self.current_bytecode_array.logicaland(left_reg, right_reg)
                    case '||=':
                        self.current_bytecode_array.logicalor(left_reg, right_reg)
                    case '*=':
                        self.current_bytecode_array.mul(left_reg, right_reg)
                    case '/=':
                        self.current_bytecode_array.div(left_reg, right_reg)
                    case '%=':
                        self.current_bytecode_array.mod(left_reg, right_reg)
                    case '+=':
                        self.current_bytecode_array.add(left_reg, right_reg)
                    case '-=':
                        self.current_bytecode_array.sub(left_reg, right_reg)
                    case '<<=':
                        self.current_bytecode_array.lshift(left_reg, right_reg)
                    case '>>=':
                        self.current_bytecode_array.rshift(left_reg, right_reg)
                    case '>>>=':
                        self.current_bytecode_array.urshift(left_reg, right_reg)
                    case '|=':
                        self.current_bytecode_array.bitwiseor(left_reg, right_reg)
                    case '&=':
                        self.current_bytecode_array.bitwiseand(left_reg, right_reg)
                    case '^=':
                        self.current_bytecode_array.bitwisexor(left_reg, right_reg)

            if node.left.computed:
                self.current_bytecode_array.setkeyedproperty(receiver, key_reg)
            else:
                self.current_bytecode_array.setnamedproperty(receiver, constant_id)
        else:
            left_reg, created, kind = self.current_scope.get_register(node.left)
            self.visit_Expression(node.right)

            if node.operator != '=':
                right_reg = self.current_scope.get_tmp_register()
                self.current_bytecode_array.star(right_reg)

                match node.operator:
                    case '&&=':
                        self.current_bytecode_array.logicaland(left_reg, right_reg)
                    case '||=':
                        self.current_bytecode_array.logicalor(left_reg, right_reg)
                    case '*=':
                        self.current_bytecode_array.mul(left_reg, right_reg)
                    case '/=':
                        self.current_bytecode_array.div(left_reg, right_reg)
                    case '%=':
                        self.current_bytecode_array.mod(left_reg, right_reg)
                    case '+=':
                        self.current_bytecode_array.add(left_reg, right_reg)
                    case '-=':
                        self.current_bytecode_array.sub(left_reg, right_reg)
                    case '<<=':
                        self.current_bytecode_array.lshift(left_reg, right_reg)
                    case '>>=':
                        self.current_bytecode_array.rshift(left_reg, right_reg)
                    case '>>>=':
                        self.current_bytecode_array.urshift(left_reg, right_reg)
                    case '|=':
                        self.current_bytecode_array.bitwiseor(left_reg, right_reg)
                    case '&=':
                        self.current_bytecode_array.bitwiseand(left_reg, right_reg)
                    case '^=':
                        self.current_bytecode_array.bitwisexor(left_reg, right_reg)

            if left_reg is not None:
                if kind == 'const':
                    raise exceptions.TypeError("Assignment to constant variable.")
                self.current_bytecode_array.star(left_reg)
            else:
                constant_id = self.constant_array.get_constant_id(
                        globals.BROKER.alloc_literal(node.left.name, 'String')
                    )
                self.current_bytecode_array.staglobal(constant_id)


    @accepted_node_types([ ast_nodes.Syntax.ObjectExpression ])
    def visit_ObjectExpression(self, node: ast_nodes.BaseNode):
        # NOTE: We create everything at runtime, while some parts could be
        # filled now... Maybe optimize it in the future?

        self.current_bytecode_array.createobject()

        # Store the object in a register
        obj_reg = self.current_scope.get_tmp_register()
        self.current_bytecode_array.star(obj_reg)

        # For each property, keep the last assignment (and keep both `getter`
                                                       # and `setter` if
                                                       # accessor type)
        props: dict[str, list[ast_nodes.BaseNode]*3] = {}
        for prop in node.properties:
            if prop.key.type is not ast_nodes.Syntax.Identifier:
                # TODO: Support literals and computed prop keys
                raise exceptions.UnsupportedException("We only support identifiers as "
                                           "keys in object literals")

            assert prop.kind in ['init', 'get', 'set']

            if prop.kind == 'init':
                props[prop.key.name] = [prop, None, None]
                continue

            # Accessor case
            curr = props.get(prop.key.name, [None] * 3)

            curr[0] = None
            curr[1 if prop.kind == 'get' else 2] = prop


        for prop_list in props.values():
            for prop in prop_list:
                if prop is None:
                    continue

                # TODO: Check what is this
                if prop.shorthand:
                    raise exceptions.UnsupportedException("Properties shorthands are not supported")

                # Parse the `value`:
                self.visit_Expression(prop.value)

                constant_id = self.constant_array.get_constant_id(
                        globals.BROKER.alloc_literal(prop.key.name, 'String')
                    )

                if prop.kind == 'init':
                    self.current_bytecode_array.setnamedproperty(obj_reg, constant_id)
                elif prop.kind == 'get':
                    self.current_bytecode_array.setgetter(obj_reg, constant_id)
                elif prop.kind == 'set':
                    self.current_bytecode_array.setsetter(obj_reg, constant_id)

        self.current_bytecode_array.ldar(obj_reg)


    @accepted_node_types([ ast_nodes.Syntax.ArrayExpression ])
    def visit_ArrayExpression(self, node: ast_nodes.BaseNode):
        # NOTE: We create everything at runtime, while some parts could be
        # filled now... Maybe optimize it in the future?

        self.current_bytecode_array.createarray(len(node.elements))

        # Store the object in a register
        obj_reg = self.current_scope.get_tmp_register()
        self.current_bytecode_array.star(obj_reg)

        index_reg = self.current_scope.get_tmp_register()

        for i, elmt in enumerate(node.elements):

            self.current_bytecode_array.ldasmi(i)
            self.current_bytecode_array.star(index_reg)

            # TODO: Introduce *holey* arrays :)
            if elmt is None:
                self.current_bytecode_array.ldaundefined()
            else:
                self.visit_Expression(elmt)
            self.current_bytecode_array.setkeyedproperty(obj_reg, index_reg)

        self.current_bytecode_array.ldar(obj_reg)


    @accepted_node_types([ ast_nodes.Syntax.MemberExpression ])
    def visit_MemberExpression(self, node: ast_nodes.BaseNode):
        self.visit_Expression(node.object)

        receiver = self.current_scope.get_tmp_register()
        self.current_bytecode_array.star(receiver)

        if node.computed:
            self.visit_Expression(node.property)
            self.current_bytecode_array.getkeyedproperty(receiver)
        else:
            constant_id = self.constant_array.get_constant_id(
                    globals.BROKER.alloc_literal(node.property.name, 'String')
                )

            self.current_bytecode_array.getnamedproperty(receiver, constant_id)

        return receiver

    @accepted_node_types([ ast_nodes.Syntax.CallExpression ])
    def visit_CallExpression(self, node: ast_nodes.BaseNode):
        target = self.current_scope.get_tmp_register()
        receiver = self.visit_Expression(node.callee)

        self.current_bytecode_array.star(target)

        if receiver is None:
            receiver = self.current_scope.get_tmp_register()
            self.current_bytecode_array.ldaundefined()
            self.current_bytecode_array.star(receiver)

        args_registers = []

        for arg in node.arguments:
            self.visit_Expression(arg)
            args_registers.append(self.current_scope.get_tmp_register())
            self.current_bytecode_array.star(args_registers[-1])

        # Check if there are holes between those registers (unlikely, but still ...)
        holes = False
        for x, y in zip(args_registers[:-1], args_registers[1:]):
            if y - x != 1:
                holes = True

        if holes:
            # Reallocate at the end
            for i in range(len(args_registers)):
                self.current_bytecode_array.ldar(args_registers[i])
                args_registers[i] = self.current_scope.get_tmp_register()
                self.current_bytecode_array.star(args_registers[i])


        self.current_bytecode_array.call(
                target,
                receiver,
                args_registers[0] if args_registers else 1,
                args_registers[-1] if args_registers else 0,
            )


    @accepted_node_types([ ast_nodes.Syntax.Program ])
    def visit_Program(self, node: ast_nodes.BaseNode):
        # Create the BytecodeArray of this program
        self.push_bytecode_array()

        # Push new scope to the scope chain
        self.push_scope()

        for child in node.body:
            self.visit_Statement(child)

        # Pop current scope from scope chain
        self.pop_scope()

        return self.pop_bytecode_array()


    @accepted_node_types([ ast_nodes.Syntax.BlockStatement ])
    def visit_BlockStatement(self, node: ast_nodes.BaseNode):
        # Push new scope to the scope chain
        self.push_scope()

        for child in node.body:
            self.visit_Statement(child)

        # Pop current scope from scope chain
        self.pop_scope()


    @accepted_node_types([ ast_nodes.Syntax.VariableDeclaration ])
    def visit_VariableDeclaration(self, node: ast_nodes.BaseNode):
        for decl in node.declarations:
            self.visit_VariableDeclarator(decl, node.kind)


    @accepted_node_types([ ast_nodes.Syntax.VariableDeclarator ])
    def visit_VariableDeclarator(self, node: ast_nodes.BaseNode, kind: str):
        id, init = node.id, node.init

        is_var = kind == 'var'

        if self.current_scope.parent:
            reg, created, res_kind = self.current_scope.get_register(id, is_var, kind)
            last_register_before = self.current_scope.last_register_index


            if reg is None:
                # Fallback to global, let runtime throw if necessary
                pass

            elif not created and (not is_var or res_kind != 'var'):
                raise exceptions.TypeError("Variable already declared.")

        if init is None:
            self.current_bytecode_array.ldaundefined()
        else:
            self.visit_Expression(init)

        if self.current_scope.parent and reg is not None:
            self.current_bytecode_array.star(reg)
            self.current_scope.shrink_to(last_register_before)
        else:
            constant_id = self.constant_array.get_constant_id(
                    globals.BROKER.alloc_literal(id.name, 'String')
                )
            self.current_bytecode_array.declareglobal(constant_id, {
                # TODO: Use an enum
                    'const': 0,
                    'let': 1,
                    'var': 2,
                }[kind])


    @accepted_node_types([ ast_nodes.Syntax.UpdateExpression ])
    def visit_UpdateExpression(self, node: ast_nodes.BaseNode):
        assert node.argument.type in [
                ast_nodes.Syntax.MemberExpression,
                ast_nodes.Syntax.Identifier
            ]


        if node.argument.type is ast_nodes.Syntax.MemberExpression:
            self.visit_Expression(node.argument.object)

            receiver = self.current_scope.get_tmp_register()
            self.current_bytecode_array.star(receiver)

            if node.argument.computed:
                key_reg = self.current_scope.get_tmp_register()
                self.visit_Expression(node.left.property)
                self.current_bytecode_array.star(key_reg)
                self.current_bytecode_array.getkeyedproperty(receiver)
            else:
                constant_id = self.constant_array.get_constant_id(
                        globals.BROKER.alloc_literal(node.argument.property.name, 'String')
                    )

                self.current_bytecode_array.getnamedproperty(receiver, constant_id)

            self.current_bytecode_array.tonumber()
            if not node.prefix:
                backup = self.current_scope.get_tmp_register()
                self.current_bytecode_array.star(backup)

            if node.operator == '++':
                self.current_bytecode_array.inc()
            else:
                self.current_bytecode_array.dec()

            if node.argument.computed:
                self.current_bytecode_array.setkeyedproperty(receiver, key_reg)
            else:
                self.current_bytecode_array.setnamedproperty(receiver, constant_id)

            if not node.prefix:
                self.current_bytecode_array.ldar(backup)
        else:
            reg, created, kind = self.current_scope.get_register(node.argument)

            if reg is None:
                constant_id = self.constant_array.get_constant_id(
                        globals.BROKER.alloc_literal(node.argument.name, 'String')
                    )

                self.current_bytecode_array.ldaglobal(constant_id)
            else:
                self.current_bytecode_array.ldar(reg)

            self.current_bytecode_array.tonumber()

            if not node.prefix:
                backup = self.current_scope.get_tmp_register()
                self.current_bytecode_array.star(backup)

            if kind == 'const':
                raise exceptions.TypeError("Assignment to constant variable.")

            if node.operator == '++':
                self.current_bytecode_array.inc()
            else:
                self.current_bytecode_array.dec()

            if reg is None:
                self.current_bytecode_array.staglobal(constant_id)
            else:
                self.current_bytecode_array.star(reg)

            if not node.prefix:
                self.current_bytecode_array.ldar(backup)

    @accepted_node_types([ ast_nodes.Syntax.UnaryExpression ])
    def visit_UnaryExpression(self, node: ast_nodes.BaseNode):
        self.visit_Expression(node.argument)
        match node.operator:
            case '+':
                self.current_bytecode_array.tonumber()
            case '-':
                self.current_bytecode_array.tonumber()
                self.current_bytecode_array.negate()
            case '~':
                self.current_bytecode_array.tonumber()
                self.current_bytecode_array.bitwisenot()
            case '!':
                self.current_bytecode_array.tobooleanlogicalnot()


    @accepted_node_types([ ast_nodes.Syntax.BinaryExpression ])
    def visit_BinaryExpression(self, node: ast_nodes.BaseNode):
        assert node.operator in [
                '*', '/', '%',
                '+', '-',
                '<<', '>>', '>>>',
                '<', '<=', '>', '>=', 'instanceof', 'in',
                '==', '!=', '===', '!==',
                '|', '&', '^'
            ]

        left_reg = self.current_scope.get_tmp_register()
        right_reg = self.current_scope.get_tmp_register()

        self.visit_Expression(node.left)
        self.current_bytecode_array.star(left_reg)

        self.visit_Expression(node.right)
        self.current_bytecode_array.star(right_reg)

        match node.operator:
            case '*':
                self.current_bytecode_array.mul(left_reg, right_reg)
            case '/':
                self.current_bytecode_array.div(left_reg, right_reg)
            case '%':
                self.current_bytecode_array.mod(left_reg, right_reg)
            case '+':
                self.current_bytecode_array.add(left_reg, right_reg)
            case '-':
                self.current_bytecode_array.sub(left_reg, right_reg)
            case '<<':
                self.current_bytecode_array.lshift(left_reg, right_reg)
            case '>>':
                self.current_bytecode_array.rshift(left_reg, right_reg)
            case '>>>':
                self.current_bytecode_array.urshift(left_reg, right_reg)
            case '<':
                self.current_bytecode_array.lessthan(left_reg, right_reg)
            case '<=':
                self.current_bytecode_array.lessthanoreq(left_reg, right_reg)
            case '>':
                self.current_bytecode_array.greaterthan(left_reg, right_reg)
            case '>=':
                self.current_bytecode_array.greaterthanoreq(left_reg, right_reg)
            case 'instanceof':
                self.current_bytecode_array.instanceof(left_reg, right_reg)
            case 'in':
                self.current_bytecode_array.inop(left_reg, right_reg)
            case '==':
                self.current_bytecode_array.looseeq(left_reg, right_reg)
            case '!=':
                self.current_bytecode_array.looseneq(left_reg, right_reg)
            case '===':
                self.current_bytecode_array.stricteq(left_reg, right_reg)
            case '!==':
                self.current_bytecode_array.strictneq(left_reg, right_reg)
            case '|':
                self.current_bytecode_array.bitwiseor(left_reg, right_reg)
            case '&':
                self.current_bytecode_array.bitwiseand(left_reg, right_reg)
            case '^':
                self.current_bytecode_array.bitwisexor(left_reg, right_reg)


    @accepted_node_types([ ast_nodes.Syntax.LogicalExpression ])
    def visit_LogicalExpression(self, node: ast_nodes.BaseNode):
        assert node.operator in ['||', '&&']

        left_reg = self.current_scope.get_tmp_register()
        right_reg = self.current_scope.get_tmp_register()

        self.visit_Expression(node.left)
        self.current_bytecode_array.star(left_reg)

        self.visit_Expression(node.right)
        self.current_bytecode_array.star(right_reg)

        match node.operator:
            case '||':
                self.current_bytecode_array.logicalor(left_reg, right_reg)
            case '&&':
                self.current_bytecode_array.logicaland(left_reg, right_reg)


    @accepted_node_types([ ast_nodes.Syntax.ConditionalExpression ])
    def visit_ConditionalExpression(self, node: ast_nodes.BaseNode):
        self.visit_Expression(node.test)
        self.current_bytecode_array.tobooleanlogicalnot()

        branch_bc_index = len(self.current_bytecode_array._bytecode_array)
        branch_over_consequent = self.current_bytecode_array.jmpif(0)

        self.visit_Expression(node.consequent)

        branch_bc_index2 = len(self.current_bytecode_array._bytecode_array)
        jmp_over_alt = self.current_bytecode_array.jmp(0)

        # Compute branch offset
        # TODO: Implement labels to make this logic easier
        offset = 0
        for bc in self.current_bytecode_array._bytecode_array[
                branch_bc_index:]:
            offset += ctypes.sizeof(bc)

        branch_over_consequent.dest_offset = offset

        self.visit_Expression(node.alternate)

        # Compute branch offset
        # TODO: Implement labels to make this logic easier
        offset = 0
        for bc in self.current_bytecode_array._bytecode_array[
                branch_bc_index2:]:
            offset += ctypes.sizeof(bc)

        jmp_over_alt.dest_offset = offset


    @accepted_node_types([ ast_nodes.Syntax.IfStatement ])
    def visit_IfStatement(self, node: ast_nodes.BaseNode):
        self.visit_Expression(node.test)
        self.current_bytecode_array.tobooleanlogicalnot()

        branch_bc_index = len(self.current_bytecode_array._bytecode_array)
        branch_over_consequent = self.current_bytecode_array.jmpif(0)

        self.visit_Statement(node.consequent)

        if node.alternate is not None:
            branch_bc_index2 = len(self.current_bytecode_array._bytecode_array)
            jmp_over_alt = self.current_bytecode_array.jmp(0)

        # Compute branch offset
        # TODO: Implement labels to make this logic easier
        offset = 0
        for bc in self.current_bytecode_array._bytecode_array[
                branch_bc_index:]:
            offset += ctypes.sizeof(bc)

        branch_over_consequent.dest_offset = offset

        if node.alternate is not None:
            self.visit_Statement(node.alternate)

            # Compute branch offset
            # TODO: Implement labels to make this logic easier
            offset = 0
            for bc in self.current_bytecode_array._bytecode_array[
                    branch_bc_index2:]:
                offset += ctypes.sizeof(bc)

            jmp_over_alt.dest_offset = offset


    @accepted_node_types([ ast_nodes.Syntax.ForStatement ])
    def visit_ForStatement(self, node: ast_nodes.BaseNode):
        self.push_scope()

        self.visit_Statement(node.init)

        before_loop_index = len(self.current_bytecode_array._bytecode_array)

        self.visit_Expression(node.test)

        self.current_bytecode_array.tobooleanlogicalnot()

        before_branch_jmp_index = len(self.current_bytecode_array._bytecode_array)
        branch = self.current_bytecode_array.jmpif(0)

        self.visit_Statement(node.body)

        self.visit_Expression(node.update)

        # Compute branch offset
        # TODO: Implement labels to make this logic easier
        offset = 0
        for bc in self.current_bytecode_array._bytecode_array[
                before_loop_index:]:
            offset += ctypes.sizeof(bc)

        self.current_bytecode_array.jmp(-offset)


        # Compute branch offset
        # TODO: Implement labels to make this logic easier
        offset = 0
        for bc in self.current_bytecode_array._bytecode_array[
                before_branch_jmp_index:]:
            offset += ctypes.sizeof(bc)

        branch.dest_offset = offset

        self.pop_scope()
