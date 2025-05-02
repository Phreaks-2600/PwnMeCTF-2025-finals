from .interpreter import interpreter # Same for `globals.INTERPRETER.*`
from . import broker # Triggers filling of `globals.BROKER`

import argparse
import ctypes
import time

from . import globals

from .interpreter import bytecode_node

from . import exceptions
from .factory import Factory
from .interpreter import bytecode_generator
from .objects import jsvalue
from .pyjsparser import parse
from .pyjsparser.std_nodes import node_to_dict
from .runtime import global_methods, hackers_toolkit
from .baseline import baseline
from .ic import getnamedproperty, setnamedproperty

class Wankel:
    def __init__(self, print_ast = False, print_bytecode = False, time_it = False):
        self.print_ast = print_ast
        self.print_bytecode = print_bytecode
        self.time_it = time_it


    def exec(self, code: str):
        if self.time_it:
            start = time.time()

        ast = parse(code)

        if self.print_ast:
            print(node_to_dict(ast))

        bc_gen = bytecode_generator.BytecodeGenerator(self.print_bytecode)

        try:
            bc_arr = bc_gen.visit_Program(ast)
        except exceptions.UnsupportedException as e:
            print(f"Unsupported exception: {e}")
            exit(-1)
        except exceptions.TypeError as e:
            print(f"TypeError: {e}")
            exit(-1)

        globals.INTERPRETER.alloc_frame(bc_arr)
        globals.INTERPRETER.run()

        if self.time_it:
            stop = time.time()
            print(stop - start)


def install_global_object():
    hack = Factory.create_js_object({
        'ftoi': Factory.create_js_builtin_function(
            hackers_toolkit.HackersFtoi.__impl__,
            1,
            globals.BROKER.alloc_literal("ftoi", "String")),
        'itof': Factory.create_js_builtin_function(
            hackers_toolkit.HackersItof.__impl__,
            1,
            globals.BROKER.alloc_literal("itof", "String")),
        'addrof': Factory.create_js_builtin_function(
            hackers_toolkit.HackersAddrOf.__impl__,
            1,
            globals.BROKER.alloc_literal("addrof", "String")),
        'fakeobj': Factory.create_js_builtin_function(
            hackers_toolkit.HackersFakeObj.__impl__,
            1,
            globals.BROKER.alloc_literal("addrof", "String")),
    })

    obj = Factory.create_js_object({
        'print': Factory.create_js_builtin_function(
            global_methods.GlobalPrint.__impl__,
            0,
            globals.BROKER.alloc_literal("print", "String")),
        'sleep': Factory.create_js_builtin_function(
            global_methods.GlobalSleep.__impl__,
            0,
            globals.BROKER.alloc_literal("sleep", "String")),
        'exit': Factory.create_js_builtin_function(
            global_methods.GlobalExit.__impl__,
            0,
            globals.BROKER.alloc_literal("exit", "String")),
        'hack': jsvalue.JSValue(jsvalue.TaggedPointer(ctypes.addressof(hack)).tagged_value),
    })

    globals.INTERPRETER_DATA.global_object = jsvalue.TaggedPointer(
            ctypes.addressof(obj))



def run():
    parser = argparse.ArgumentParser(
            prog="wankel",
            description="Simplified JavaScript Engine for Educational Purpose",
        )

    parser.add_argument("--source", type=argparse.FileType("r"))
    parser.add_argument("--source-from-stdin", action="store_true")
    parser.add_argument("--print-ast", action="store_true")
    parser.add_argument("--print-bytecode", action="store_true")
    parser.add_argument("--time-it", action="store_true")
    args = parser.parse_args()

    wankel = Wankel(
            print_ast = args.print_ast,
            print_bytecode = args.print_bytecode,
            time_it = args.time_it,
        )

    install_global_object()
    baseline.Baseline.init()

    if args.source_from_stdin:
        source = ""

        while (line := input()) != "__END__":
            source += line + "\n"

        wankel.exec(source)
    elif args.source:
        wankel.exec(args.source.read())
    else:
        while True:
            wankel.exec(input("> "))

