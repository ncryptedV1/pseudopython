r'!tex \Require{Roadmap $G$, edge length $D(u, v)$, visible faces $S(u, v)$.}'
r'!tex \Require{Root state $v_0$, and faces seen $S_0$}.'

def Search(G, S_0, v_0):
#    #S_G = (r'\cup_{e\in{}E} \, S_e'); r'All faces visible somewhere in G.'
    d[0], q[0], D[0] = 0; 'Depth, score, and distance.'
    #U[0] = r'$\{u, v \in E_G \, : \, u = v_0\}$'
    #U[0] = {v[0] in e for e in E_G}; 'Unvisited neighbors at root'
    U[0] = 'Neighbors'(G, v_0); 'Unvisited neighbors.'
    for i in range(1, N['iter']):
      with rlap(phantom=D[i]):
        #u = r'${\arg\min_{\, u \, : \, U_u \neq \, \emptyset}}$ ' @ d[u]
        p[i] = r'\arg\min'[v @ ':' @ U[v] != '\emptyset'](d[v]); r'Most shallow leaf.\footnote{Taking the most shallow leaf, i.e. leaf of smallest depth, results in a BFS-like search order. An alternative is to minimize the distance $D_u$ instead, however, that would effectively prevent searching beyond jump edges as the distance would be significantly higher.}'
        #p[i] = u; '$u$ is parent of $i$'
        v[i] = 'Pick'(U[p[i]])
        d[i] = d[p[i]] + 1
        D[i] = D[p[i]] + D(v[p[i]], v[i])
        S[i] = S[p[i]] @ r' $\cup$ ' @ S(v[p[i]], v[i])
        q[i] = q[p[i]] + s(S[i], D[i])
# g(S[i]) @ '$\,\exp$'(-Sym_lambda @ D[i]) 
        U[i] = 'Neighbors'(G, v_i)
        U[p[i]] = U[p[i]] @ r' $\setminus$ ' @ {v[i]}
    return 'Path'(r'\arg\max'[v](q[v]))


'!hide'
if __name__ == '__main__':
    import pseudopython
    pseudopython.main()
