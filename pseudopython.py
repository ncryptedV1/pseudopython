import sys
import ast
import argparse
from os import path, rename, makedirs
from subprocess import check_call
from contextlib import contextmanager


def symbolify(name):
    if name.startswith('Sym_'):
        return '\\' + name[4:]
    elif name.startswith('MC_'):
        return '\\mathcal{' + name[3:] + '}'
    elif name.startswith('BB_'):
        return '\\mathbb{' + name[3:] + '}'
    return name


class Visitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self._emit_tex = True
        self.flags = {}
        self._indentation = 0
        self._lines = []

    def line(self, line):
        self._lines.append((line, self._indentation))

    def _indented_lines(self):
        for line, indentation in self._lines:
            yield '  ' * indentation + line + '\n'

    @contextmanager
    def indent(self):
        self._indentation += 1
        yield
        self._indentation -= 1

    def __str__(self):
        return ''.join(self._indented_lines())

    def generic_visit(self, node):
        return '?'

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def body(self, body):
        with self.indent():
            for node in body:
                self.visit(node)

    def arg(self, a):
        if a.annotation is None:
            return r'\PyArg{' + symbolify(a.arg) + '}'
        else:
            assert isinstance(a.annotation, ast.Str)
            return r'\PyArgAnnotation{' + symbolify(a.arg) + '}{' + a.annotation.s + '}'

    def expr(self, e):
        return r'\PyExpr{' + self.visit(e) + '}'

    def visit_FunctionDef(self, node):
        if not self._emit_tex:
            return
        args = r'\PyArgSep'.join(self.arg(a) for a in node.args.args)
        if node.returns:
            self.line(r'\Function{' + node.name + '}{' + args +
                      r'}{ $\rightarrow$ \texttt{' + node.returns.s + '}}')
            self.body(node.body)
            self.line(r'\EndFunction%')
        else:
            self.line(r'\Procedure{' + node.name + '}{' + args + '}')
            self.body(node.body)
            self.line(r'\EndProcedure%')

    def visit_Assign(self, node):
        if not self._emit_tex:
            return
        targets = r', '.join(self.visit(target) for target in node.targets)
        value   = self.visit(node.value)
        if self.flags.get('overlap') == 'rlap':
            phantom = self.flags['phantom']
            self.line(r'\State{\PyAssign{\rlap{' + targets + '}' + r'\hphantom{' + phantom + r'}}{' + value + '}}')
        else:
            self.line(r'\State{\PyAssign{' + targets + '}{' + value + '}}')

    def visit_AnnAssign(self, node):
        if not self._emit_tex:
            return

        target = self.visit(node.target)

        assert isinstance(node.annotation, ast.Str)
        assert node.value == None

        assign = r'\PyAnnotation{' + target + '}{' + node.annotation.s + '}'

        self.line(r'\State{' + assign + '}')

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Str):
            self.handle_magic_string(node.value.s)
            return
        if not self._emit_tex:
            return
        self.line(r'\State{' + self.expr(node.value) + '}')

    def handle_magic_string(self, s: str):
        if s.startswith('!tex'):
            for l in s[4:].splitlines():
                self.line(l)
        elif s == '!show':
            self._emit_tex = True
        elif s == '!hide':
            self._emit_tex = False
        else:
            self.line(r'\Comment{' + s + '}')

    def visit_Str(self, node):
        return '{' + node.s + '}'

    def visit_Name(self, node):
        return r'\PyName{' + symbolify(node.id) + '}'

    def visit_Num(self, node):
        return r'\PyNum{' + str(node.n) + '}'

    def visit_NameConstant(self, node):
        return r'\Py' + str(node.value) + '{}'

    def visit_BoolOp(self, node):
        return (r' \Py' + type(node.op).__name__ + '{} ').join(self.visit(v) for v in node.values)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == '_':
            assert len(node.args) == 1
            [arg] = node.args
            return r'\PyPar{' + self.visit(arg) + '}'

        return r'\PyCall{' + self.visit(node.func) + '}' + '{' + r', '.join(self.visit(a) for a in node.args) + '}'

    def visit_For(self, node):
        if not self._emit_tex:
            return

        assert isinstance(node.iter, ast.Call)
        assert isinstance(node.iter.func, ast.Name)
        assert node.iter.func.id == 'range'

        nargs = len(node.iter.args)
        args = map(self.visit, node.iter.args)
        assert 1 <= nargs <= 3
        if nargs == 1:
            start = r'\PyNum{0}'
            [stop] = args
            step = r'\PyNum{1}'
        if nargs == 2:
            [start, stop] = args
            step = r'\PyNum{1}'
        if nargs == 3:
            [start, stop, step] = args

        variable = self.visit(node.target)

        self.line(
            r'\PyFor' + ''.join('{' + x + '}' for x in [variable, start, stop, step]))
        self.body(node.body)
        if node.orelse:
            self.line(r'\PyForElse')
            self.body(node.orelse)
        self.line(r'\PyEndFor')

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.MatMult):
            return self.visit(node.left) + self.visit(node.right)
        return r'\Py' + type(node.op).__name__ + '{' + self.visit(node.left) + '}{' + self.visit(node.right) + '}'

    def visit_UnaryOp(self, node):
        return r'\Py' + type(node.op).__name__ + '{' + self.visit(node.operand) + '}'

    def visit_Subscript(self, node):
        return r'\PySubscript{' + self.visit(node.value) + '}{' + self.visit(node.slice) + '}'

    def visit_Index(self, node):
        return self.visit(node.value)

    def visit_Compare(self, node):
        result = self.visit(node.left)
        for op, right in zip(node.ops, node.comparators):
            result += r' \Py' + type(op).__name__ + '{} ' + self.visit(right)
        return result

    def visit_If(self, node, else_=False):
        if not self._emit_tex:
            return
        name = r'\ElsIf' if else_ else r'\If'
        self.line(name + '{' + self.expr(node.test) + '}')
        self.body(node.body)
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self.visit_If(node.orelse[0], else_=True)
        elif len(node.orelse) > 0:
            self.line(r'\Else%')
            self.body(node.orelse)
        if not else_:
            self.line(r'\EndIf%')

    def visit_While(self, node):
        if not self._emit_tex:
            return
        self.line(r'\While{' + self.expr(node.test) + '}')
        self.body(node.body)
        self.line(r'\EndWhile%')

    def visit_Return(self, node):
        if not self._emit_tex:
            return
        self.line(r'\Return{' + (self.expr(node.value) if node.value else '') + '}')

    def visit_List(self, node):
        elts = r', '.join(self.visit(el) for el in node.elts)
        return r'\PyList{' + elts + '}'

    def visit_Tuple(self, node):
        elts = r', '.join(self.visit(el) for el in node.elts)
        if isinstance(node.ctx, ast.Store):
            return elts
        elif len(node.elts) == 1:
            return r'({' + elts + r'},)'
        else:
            return r'({' + elts + r'})'

    def visit_Set(self, node):
        elts = r', '.join(self.visit(el) for el in node.elts)
        return r'$\{$' + elts + '$\}$'

    def visit_SetComp(self, node):
        assert len(node.generators) == 1
        gen = node.generators[0]
        with self.indent():
            rhs = self.visit(node.elt)
            tgt = self.visit(gen.target) if gen.target.id != '_' else rhs
            it  = self.visit(gen.iter)
            lhs = ', '.join([tgt + ' $\in$ ' + it] + [self.visit(if_) for if_ in gen.ifs])
            return r'$\{$' + lhs + r' $:$ ' + rhs + r'$\}$'

    def visit_With(self, node):
        with self.pushed_flags(**self.flags):
            for item in node.items:
                call = item.context_expr
                assert isinstance(call, ast.Call)
                name = item.context_expr.func
                assert isinstance(name, ast.Name)
                kwds = {kw.arg: self.visit(kw.value) for kw in call.keywords}
                if name.id in {'rlap', 'llap'}:
                    self.flags['overlap'] = name.id
                    self.flags['phantom'] = kwds['phantom']
            self.body(node.body)

    @contextmanager
    def pushed_flags(self, **flags):
        prev = self.flags.copy()
        try:
            self.flags = flags
            yield
        finally:
            self.flags = prev


def source_to_pseudocode(source):
    vis = Visitor()
    vis.visit(ast.parse(source))
    return str(vis)


def preamble(s):
    return r"""
\documentclass[border=0.5cm, 12pt]{standalone}

\usepackage[utf8]{inputenc}
\usepackage{amsmath,amsfonts}
\usepackage[section]{algorithm}
\usepackage{algorithmicx}
\usepackage[noend]{algpseudocode}
\usepackage{pseudopython}

\begin{document}
\begin{minipage}{13cm}
    \begin{algorithmic}[1]
""" + s + r"""
    \end{algorithmic}
\end{minipage}
\end{document} 
"""


parser = argparse.ArgumentParser()
parser.add_argument('--pdf', help='Produce a PDF', default=None)
parser.add_argument('--png', help='Produce a PNG', default=None)
parser.add_argument('--only-print', help='Only print the pseudocode', action='store_true', default=False)
parser.add_argument('--standalone', help='Print preamble and all that jazz', action='store_true', default=False)


def main():
    args = parser.parse_args()
    args.pathname = sys.argv[0]
    run(args)


def run(args):
    vis = Visitor()

    with open(args.pathname) as f:
        vis.visit(ast.parse(f.read()))

    out_path = path.join(path.dirname(args.pathname),
                         '.pseudopython',
                         path.basename(args.pathname))

    out_pdf_pathname = path.join(out_path, 'pseudopython.pdf')
    makedirs(out_path, exist_ok=True)

    if args.png or args.pdf:
        with open(path.join(out_path, 'pseudopython.tex'), 'w') as f:
            f.write(preamble(str(vis)))
        texinputs = ':'.join(['.', path.dirname(__file__), ''])
        cmd = ['/usr/bin/pdflatex', '-halt-on-error', 'pseudopython.tex', '-pdf']
        check_call(cmd, cwd=out_path, env={'TEXINPUTS': texinputs})
        print('pdflatex build finished in', out_path)

    print()

    if args.png:
        check_call(['pdftoppm', '-singlefile', '-png', 'pseudopython.pdf', 'pseudopython'], cwd=out_path)
        rename(path.join(out_path, 'pseudopython.png'), args.png)
        print('PNG at file://' + path.abspath(args.png))

    if args.pdf:
        rename(out_pdf_pathname, args.pdf)
        print('PDF at file://' + path.abspath(args.pdf))

    if not (args.pdf or args.png):
        print(preamble(str(vis)) if args.standalone else str(vis), end='')


if __name__ == '__main__':
    parser.add_argument('pathname', help='Python code to convert')
    run(parser.parse_args())
