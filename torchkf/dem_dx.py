import torch 
import warnings
import numpy as np

from typing import Tuple

from .dem_structs import *
from .dem_symb import *


# necessary for sympy + numpy
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)


def compute_df_d2f(func, inputs, input_keys=None) -> Tuple[dotdict, dotdict]:
    """ compute first- and second-order derivatives of `func` evaluated at `inputs`.
    inputs must be 1 or 2d, func must return 1 or 2d tensors 
    Returns a tuple of (df, d2f) where: 
    df.dk is the derivative wrt input indexed  by input key 'dk'
    d2f.di.dj is the 2nd-order derivative wrt inputs 'di' and 'dj'. 
    """
    # This is deprecated in favor of symbolic differentiation

    raise NotImplementedError()

    if input_keys is None:
        input_keys = [f'dx{i}' for i in range(len(inputs))]
    else: 
        assert(len(input_keys) == len(inputs))

    def handle_shapes(inputs):
        xs     = []
        for x in inputs:
            if any(_ == 0 for _ in x.shape) or len(x.shape) == 0: 
                xs.append(torch.empty(0))
            elif len(x.shape) == 1:
                xs.append(x)
            elif x.shape[0] == x.shape[1] == 1: 
                xs.append(x.squeeze(1))
            else:
                xs.append(x.squeeze())
        return tuple(xs)
    
    inputs = handle_shapes(inputs)
    
    Ji = torch.autograd.functional.jacobian(func, inputs)
    df = dotdict()
    for i in range(len(inputs)): 
        if all(_ > 0 for _ in Ji[i].shape):
            df[input_keys[i]] = Ji[i].reshape((-1, inputs[i].shape[0]))
        else: 
            df[input_keys[i]] = torch.empty(0)
    # dim 1 of J are df[:]/dx[i]
    # dim 2 of J are df[j]/dx[:]
    
    d2f = dotdict()
    for i in range(len(inputs)): 
        # Compute d/dxj(dfdxi)
        Hi = torch.autograd.functional.jacobian(
                lambda *x: torch.autograd.functional.jacobian(func, x)[i], 
                inputs, vectorize=True)
        Hij = dotdict()
        for j in range(len(inputs)): 
            if all(_ > 0 for _ in Hi[j].shape):
                Hij[input_keys[j]] = Hi[j]
            else: 
                Hij[input_keys[j]] = torch.empty(0)
        d2f[input_keys[i]] = Hij
    # dim 1 of H are df[i]/d(x[:]x[:])
    # dim 2 of H are df[:]/d(x[i]x[:])
    # dim 3 of H are df[:]/d(x[:]x[j])
    # d2f is (Nf, Na, Nb)
    return df, d2f

def compute_dx(f, dfdx, t, isreg=False): 
    # Adapted from spm_dx
    # Compute updates using local linearization (Ozaki 1985)

    if len(f.shape) == 1: 
        f = f[..., None]

    # if isreg we use t as a regularization parameter   
    if isreg:
        t  = np.exp(t - np.linalg.slogdet(dfdx)[1] / f.shape[0])

    if f.shape[0] != dfdx.shape[0]: 
        raise ValueError(f'Shape mismatch: first dim of f {f.shape} must match that of df/dx {dfdx.shape}.')

    if len(f) == len(dfdx) == 0:
        return np.array([[]])

    # use the exponentiation trick to avoid inverting dfdx
    J  = block_matrix([
        [np.zeros((1,1)),       []], 
        [          f * t, dfdx * t]
    ])
    dx = torch.matrix_exp(torch.from_numpy(J)).numpy()

    return dx[1:, 0, None]





