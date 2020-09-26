# Write Algorithms for LaTex in Python

Writing pseudocode is surprisingly arcane. Wikipedia typically uses
Python-like syntax, so why not generate the relevant algorithmx LaTeX commands
from that?

Install it now. No dependencies, only Python 3.x.

    pip install git+https://github.com/lericson/pseudopython.git

Pseudopython basically lets you put strings anywhere you'd like so long as
they're syntactically valid.

    f = '$\arg\min_i$'(A[i])

Works fine and outputs what you'd expect. Also, the pseudo-Python scripts,
being syntactically valid, can be made "executable" by adding

```python
'!hide'  # Exclude code below from pseudocode printout
if __name__ == '__main__':
    import pseudopython
    pseudopython.main()
```

Which is convenient. You can thus think of the scripts as using their own code
to produce pseudo-code. It's all very Lisp-like. 

You can produce test PDFs to look at the result:

    python3 my_pseudocode.py --pdf test.pdf

... would produce a `test.pdf` in the current directory.

Take a look in the examples directory for more. There should be at least one
real-life example.

When using the pseudocode in your actual document, you need to
`\usepackage{pseudopython}` and place the `pseudopython.sty` file someplace
that your TeX installation finds. On Overleaf, for example, you can just upload
it, and it works. Locally, this works with the file in `my/dir`:

    TEXINPUTS=.:my/dir: pdflatex my.tex -pdf

**Note:** The trailing colon is important. Typically you'd create `myalgo.tex`
from the output, and then use `\input` like below:

```latex
% your \documentclass, maybe some good vibe comments, etc

\usepackage{algorithm}
\usepackage{algorithmicx}
\usepackage[noend]{algpseudocode}
\usepackage{pseudopython}

% \begin{document} and all that jazz

\begin{algorithm} % or whatever you prefer
  \caption{Programmer? I hardly know 'er}
  \label{alg:myalgo}
  \begin{algorithmic}[1]
    \input{myalgo}
  \end{algorithmic}
\end{figure}

% rest of your document
```
