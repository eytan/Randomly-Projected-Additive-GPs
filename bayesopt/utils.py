from math import pi

import numpy as np
import torch
import gpytorch
import gp_models

def stybtang(x: torch.Tensor):
    return 1/2 * torch.sum(x.pow(4) - 16*x.pow(2) + 5*x, dim=-1)


def np_stybtang(x: np.array):
    return 1/2 * np.sum(np.power(x, 4) - 16*np.power(x, 2) + 5 * x, axis=-1)


def michalewicz(x: torch.Tensor, m: int):
    d = x.shape[-1]
    scaled_x = x * torch.arange(1, d+1, dtype=torch.float).unsqueeze(0)
    return -torch.sum(torch.sin(x) * torch.sin(scaled_x / pi).pow(2*m), dim=-1)


def np_michalewicz(x: np.array, m: int):
    d = x.shape[-1]
    scaled_x = x * np.arange(1, d+1, dtype=np.float)
    return -np.sum(np.sin(x) * np.power(np.sin(scaled_x / pi), 2*m), axis=-1)


def mixture_of_gaussians(x: torch.Tensor, mixtures, degree, sigma):
    shape = x.shape
    d = shape[-1]
    toreturn = torch.zeros(*shape[:-1])
    for i in range(mixtures):
        thisdeg = min(degree, d-i)
        mu = torch.zeros(degree)
        mu[0] = 1
        parts = x.index_select(dim=-1, index=torch.tensor([idx for idx in range(i, i+thisdeg)]))
        sqdist = torch.norm(parts - mu, dim=-1).pow(2)
        gauss = torch.exp(-1/(2*sigma**2) * sqdist) * i
        toreturn += gauss
    return -toreturn


def random_branin(x: torch.Tensor):
    """Branin randomly embedded into 2 dims of a larger vector"""
    d = x.shape[-1]
    torch.random.manual_seed(123456)
    i = torch.randint(0, d)
    j = torch.randint(0, d-1)
    if j >= i:  # easy way to choose 2 numbers w/o replacement
        j += 1
    return branin(x.index_select(dim=-1, index=torch.tensor([i,j])))


def branin(x: torch.Tensor):
    x1 = x.index_select(-1, torch.tensor(0))
    x2 = x.index_select(-1, torch.tensor(1))
    comp1 = (x2 - 5.1 / (4 * pi**2) * x1.pow(2) + 5/pi * x1 - 6).pow(2)
    comp2 = 10*(1-1/(8*pi))*torch.cos(x1) + 10
    return comp1 + comp2


def embed_function(f, f_dim, new_dim, A=None):
    if A is None:
        A = torch.randn(new_dim, f_dim)
    def new_f(x):
        return f(x.matmul(A))
    return new_f


def easy_meshgrid(sizes, numpy=False, interior=True):
    spot_per_dim = []
    for i in range(len(sizes)):
        if interior:
            spots = torch.linspace(0, 1, sizes[i] + 2)[1:-1]
        else:
            spots = torch.linspace(0, 1, sizes[i])
        spot_per_dim.append(spots)
    tensors = torch.meshgrid(spot_per_dim)
    stacked = torch.stack(tensors)
    res = stacked.reshape(len(sizes), -1).t()
    if numpy:
        res = res.numpy()
    return res


def get_lengthscales(kernel):
    if isinstance(kernel, gpytorch.kernels.ScaleKernel):
        return get_lengthscales(kernel.base_kernel)
    elif kernel.has_lengthscale:
        return kernel.lengthscale
    elif isinstance(kernel, gp_models.GeneralizedProjectionKernel):
        ls = []
        for k in kernel.kernel.kernels:
            ls_ = []
            for kk in k.base_kernel.kernels:
                ls_.append(kk.lengthscale.item())
            ls.append(ls_)
        return ls
    else:
        return None


def get_mixins(kernel):
    if isinstance(kernel, gp_models.GeneralizedProjectionKernel):
        mixins = []
        for k in kernel.kernel.kernels:
            mixins.append(k.outputscale.item())
        return mixins
    elif isinstance(kernel, gpytorch.kernels.ScaleKernel):
        return get_mixins(kernel.base_kernel)
    else:
        return None


def format_for_str(num_or_list, decimals=3):
    if isinstance(num_or_list, list):
        return [format_for_str(n) for n in num_or_list]
    elif isinstance(num_or_list, float):
        return np.round(num_or_list, decimals)
    else:
        return ''


def get_outputscale(kernel):
    if isinstance(kernel, gpytorch.kernels.ScaleKernel):
        return kernel.outputscale
    else:
        return None