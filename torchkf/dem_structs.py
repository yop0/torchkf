import numpy as np
import sympy
import math


try:
    from math import prod
except ImportError: 
    from functools import reduce
    import operator
    def prod(iterable):
        return reduce(operator.mul, iterable, 1)

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class cdotdict(dotdict):
    """callable dot dict""" 
    def __call__(self, *args, **kwargs):
        return dotdict(
            zip(self.keys(),
                map(lambda v: 
                    v(*args, **kwargs) if callable(v) else v, 
                    self.values())))
        
def kron(a, b): 
    m, n = a.shape
    p, q = b.shape
    M, N = m * p, n * q
    return (a.reshape((m, 1, n, 1)) * b.reshape((1, p, 1, q))).reshape((M, N))

def kron_eye(A, N, M=None):  # Simulates np.kron(np.eye(N, M), A)
    m, n = A.shape    
    if M is None: 
        out = np.zeros((N,m,N,n), dtype=A.dtype)
        diag = np.einsum('ijik->ijk',out)
        diag[:] = A
        out.shape = (m*N,n*N)

    else: 
        K   = N if N >= M else M
        out = np.zeros((K,m,K,n), dtype=A.dtype)
        diag = np.einsum('ijik->ijk',out)
        diag[:] = A
        out = out[:N,:,:M,:] 
        out.shape = (m*N,n*M)
        
    return out

def block_diag(*arrs): 
    m, n = 0, 0
    for arr in arrs: 
        m += arr.shape[0]
        n += arr.shape[1]
    ret = np.zeros((m, n))
    nx,ny = 0,0
    for arr in arrs: 
        ni,nj = arr.shape
        ret[nx:nx+ni,ny:ny+nj] = arr
        nx += ni
        ny += nj
    return ret


def block_matrix(nested_lists): 
    row_sizes = [0] * len(nested_lists)
    col_sizes = [0] * len(nested_lists[0])

    for i, row in enumerate(nested_lists): 
        if len(row) != len(col_sizes): 
            raise ValueError(f'Invalid number of columns at row {i + 1}:'
                             f' expected {len(col_sizes)}, got {len(row)}.')

        M = row_sizes[i]
        for j, e in enumerate(row): 
            if len(e):
                m, n = e.shape
                N = col_sizes[j]
                    
                # check for height
                if M and m != M: 
                        raise ValueError('Unable to build block matrix: the number of rows at block-index ({},{}) (shape {}) does not match that of the previous block (expected {}).'.format(i,j,e.shape,row_sizes[i]))

                # check for width
                if N and n != N: 
                        raise ValueError('Unable to build block matrix: the number of columns at block-index ({},{}) (shape {}) does not match that of the previous block (expected {}).'.format(i,j,e.shape,col_sizes[j]))

                row_sizes[i], col_sizes[j] = m, n
                    
    M = sum(row_sizes)
    N = sum(col_sizes)
    
    out = np.zeros((M, N))
    i = 0
    for I, nx in enumerate(row_sizes): 
        j  = 0
        for J, ny in enumerate(col_sizes):
            e  = nested_lists[I][J]
            if len(e): 
                out[i:i+nx,j:j+ny] = e
            j += ny
        i += nx
    return out


class cell(list): 
    def __init__(self, m, n): 
        super().__init__([[] for j in range(n)] for i in range(m))
    
    def __getitem__(self, index): 
        if isinstance(index, tuple): 
            i, j = index
            return self[i][j]
        else: 
            return super().__getitem__(index)
    
    def __setitem__(self, index, value): 
        if isinstance(index, tuple): 
            i, j = index
            xi = self[i]
            xi[j] = value
            self[i] = xi
        else: 
            super().__setitem__(index, value)



# from functools import wraps
# import torch 
# def vfunc(in_sizes, out_size): 
#     """ wraps a function of column vectors that return a column vector
#      handles conversion from torch to numpy
#      shapes is a list of number of rows (int) for each vector 
#     """
#     def _decorator(func):
#         @wraps(func)
#         def _wrapped(*args): 
#             cargs = []
#             for i, (arg, size) in enumerate(zip(args, in_sizes)): 
#                 if not isinstance(arg, np.ndarray): 
#                     arg = arg.numpy()
#                 cargs.append(arg.reshape((size, 1)))

#             ret = func(*cargs)
#             return torch.from_numpy(ret.reshape((out_size, 1)))
#         return _wrapped
#     return _decorator
