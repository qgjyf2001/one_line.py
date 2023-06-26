import ast
import sys

def parse_str(s):
    return ast.parse(s).body[0].value

func_expr_map = {}
class FuncVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        func_expr_map[node.name] = ast.Lambda(args=node.args,body = ast.Constant(value = None))
class CallTransformer(ast.NodeTransformer):
    def __init__(self):
        self.stack = []
    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        node = ast.NodeTransformer.generic_visit(self, node)
        self.stack.pop()
        return node
    def visit_Call(self, node):
        func = node.func
        if isinstance(func,ast.Name) and func.id in func_expr_map.keys():
            if len(self.stack) == 0 or self.stack[-1]!=func.id:
                node.func = func_expr_map[func.id]
        return ast.NodeTransformer.generic_visit(self, node)
            
code = open(sys.argv[1],"r").read()
root=ast.parse(code)

FuncVisitor().visit(root)
CallTransformer().visit(root)

def get_func_expr(exprs,nodes,default_value):
    class Context:
        def __init__(self):
            self.expr = None
    ctx = Context()
    if len(exprs)==0 or (exprs[-1] is not None and not isinstance(exprs[-1], ast.Expr)):
        exprs.append(default_value)
    ctx.expr = exprs[-1]
    for expr_func,node in zip(exprs[-2::-1],nodes[::-1]):
        ctx.expr = expr_func(ctx.expr,node)
    return ctx.expr

def gen_import_expr(exprs, node, gen_args):
    outs = []
    for submodule in node.names:
        out_name = submodule.asname
        if (out_name == None):
            out_name = submodule.name
        outs.append(ast.arg(arg = out_name))
    exprs.append(lambda expr, node: ast.Call(
        func = ast.Lambda(args=ast.arguments(args = outs,posonlyargs = [],kwonlyargs= [],defaults = []),body = expr),
        args = [parse_str(gen_args(node,submodule)) for submodule in node.names],
        keywords = []
    ))
def gen_assign_expr(exprs,node):
    if (len(node.targets) == 1):
        target = node.targets[0]
        if isinstance(target,ast.Tuple):
            outs = []
            for name in target.elts:
                outs.append(ast.arg(arg = name.id))
            exprs.append(lambda expr, node:ast.Call(
                func = ast.Lambda(args = ast.arguments(args = outs,posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
                args = [ast.Starred(value = node.value)],
                keywords = []
             ))
        elif isinstance(target,ast.Name):
            exprs.append(lambda expr, node: ast.Call(
                func = ast.Lambda(args = ast.arguments(args = [ast.arg(target.id)],posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
                args = [node.value],
                keywords = []
            ))
        elif isinstance(target,ast.Attribute):
            exprs.append(lambda expr, node: ast.Call(
                func = ast.Lambda(args = ast.arguments(args = [ast.arg(arg = "_")],posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
                args = [
                    ast.Call(
                        func = ast.Name(id = 'setattr'),
                        args = [
                            target.value,
                            ast.Constant(target.attr),
                            node.value
                        ],
                        keywords = []
                    )
                ],
                keywords = []
            ))
        elif isinstance(target,ast.Subscript):
            exprs.append(lambda expr, node: ast.Call(
                func = ast.Lambda(args = ast.arguments(args = [ast.arg(arg = "_")],posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
                args = [
                    ast.Call(
                        func = ast.Attribute(value = target.value,attr = "__setitem__"),
                        args = [
                            target.slice,
                            node.value
                        ],
                        keywords = []
                    )
                ],
                keywords = []
            ))
        else:
            print("assign:unsupport type")
            print(target)
            pass # TODO support more types
    else:
        print("unknown")
        pass # unknown
 
def gen_class_expr(exprs,node,gen_expr_func):
    init_codes = []
    func_map = {}
    for stat in node.body:
        if isinstance(stat, ast.FunctionDef):
            func_expr = gen_expr_func(stat, ast.Constant(value = None))
            func_map[stat.name] = ast.Lambda(
                body = func_expr,
                args = stat.args
            )
        else:
            init_codes.append(stat)
    func_list = []
    for func_name in func_map:
        func_list.append(f'"{func_name}":{ast.unparse(func_map[func_name])}')
    if len(node.bases) == 0:
        base_list = ["object"]
    else:
        base_list = [ast.unparse(base) for base in node.bases]
    exprs.append(lambda expr, node: ast.Call(
        func = ast.Lambda(args = ast.arguments(args = [ast.arg(node.name)],posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
        args = [parse_str(f"{node.name} = type('{node.name}', ({','.join(base_list)},),{{{','.join(func_list)}}})")],
        keywords = []
    ))
def gen_for_expr(exprs,node,gen_expr_func):
    for_expr = gen_expr_func(node, ast.Constant(value = None))
    arg = ast.ListComp(
        generators = [ast.comprehension(target = node.target, iter = node.iter, ifs = [], is_async = 0)],
        elt = for_expr
        )
            
    exprs.append(lambda expr,node : ast.Call(
    func = ast.Lambda(args = ast.arguments(args = [ast.arg("_")],posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
        args = [ast.ListComp(
            generators = [ast.comprehension(target = node.target, iter = node.iter, ifs = [], is_async = 0)],
            elt = for_expr
        )],
        keywords = []
    ))
def gen_arg_str(num):
    return ','.join([f'__arg{i} 'for i in range(num)])

def gen_expr(root, default_value):
    class Context:
        def __init__(self):
            self.default_value = None
    exprs = []
    nodes = []
    ctx = Context()
    ctx.default_value = default_value
    for node in root.body:
        nodes.append(node)
        if isinstance(node,ast.ImportFrom):
            gen_import_expr(exprs, node, lambda node,submodule:f'__import__("{node.module}", [], [], ["{submodule.name}"]).{submodule.name}')
        elif isinstance(node,ast.Import):
            gen_import_expr(exprs, node, lambda node,submodule:f'__import__("{submodule.name}")')
        elif isinstance(node,ast.Assign):
            gen_assign_expr(exprs,node)
        elif isinstance(node,ast.FunctionDef):
            nodes.pop()
            func_expr = gen_expr(node, ast.Constant(value = None))

            args_str = gen_arg_str(len(node.args.args))
            Y_combiner = parse_str(f'lambda __f: (lambda __x: __x(__x))(lambda __x: __f(lambda {args_str}: __x(__x)({args_str})))')
            func = func_expr_map[node.name]
            func.body = ast.Call(
                args = node.args.args,
                func = ast.Call(
                    func = Y_combiner,
                    args = [ast.Lambda(
                        args = ast.arguments(args = [ast.arg(node.name)],posonlyargs = [],kwonlyargs= [],defaults = []), body = 
                            ast.Lambda(
                                args = node.args,
                                body = func_expr
                            )
                        )],
                    keywords = []
                ),
                keywords = []
            )
        elif isinstance(node, ast.ClassDef):
            gen_class_expr(exprs,node,gen_expr)
        elif isinstance(node, ast.Return):
            nodes.pop()
            ctx.default_value = node.value
            #return get_func_expr(exprs,nodes,node.value)
        elif isinstance(node, ast.For):
            gen_for_expr(exprs,node,gen_expr)
        elif isinstance(node, ast.If):
            exprs.append(lambda expr, node:ast.IfExp(
                test = node.test,
                body = gen_expr(node, expr),
                orelse = gen_expr(ast.Lambda(body = node.orelse), expr)))
        elif isinstance(node,ast.Expr):
            exprs.append(lambda expr, node:ast.Call(
                func = ast.Lambda(args = ast.arguments(args = [ast.arg("_")],posonlyargs = [],kwonlyargs= [],defaults = []), body = expr),
                args = [node.value],
                keywords = []
            ))
        elif isinstance(node,ast.Pass):
            nodes.pop()
        else:
            print("unsupported type:")
            print(node)
    return get_func_expr(exprs, nodes, ctx.default_value)
expr = gen_expr(root,ast.Constant(value = None) )
open("out.py","w").write(ast.unparse(expr))
