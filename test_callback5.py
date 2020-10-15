import os
import string
import subprocess

import cupy as cp
from cupyx.scipy.fftpack import get_fft_plan



code = r'''
#include <cufft.h>
#include <cufftXt.h>


__device__ cufftComplex CB_ConvertInputC(
    void *dataIn, 
    size_t offset, 
    void *callerInfo, 
    void *sharedPtr) 
{
    //cufftComplex x{1., 0.};
    cufftComplex x;
    x.x = 1.;
    x.y = 0.;
    //return cuCaddf(((cufftComplex*)dataIn)[offset], x);
    return x;
}

__device__ 
cufftCallbackLoadC d_loadCallbackPtr = CB_ConvertInputC;
'''

mod = cp.RawModule(code=code,
                   backend='nvcc',
                   #options=('-lcufft_static', '-lculibos', '-dc',))
                   options=('-dc',))
#sym = mod.get_global('CB_ConvertInputC')
#sym = mod.get_global('d_loadCallbackPtr')
sym = mod.get_function('CB_ConvertInputC')
print(sym.ptr)
#a = cp.random.random((64, 64, 64)).astype(cp.complex64)
a = cp.random.random((64, 128)).astype(cp.complex64)
plan = get_fft_plan(a, axes=(1,))
mgr = cp.cuda.cufft.CallbackManager()
print((plan.nx, plan.fft_type, plan.batch))
handle = mgr.set_callback(('Plan1d', (plan.nx, plan.fft_type, plan.batch)), sym.ptr, 0)
b = plan.get_output_array(a)
print(a.dtype, a.shape, b.dtype, b.shape)
mgr.transform(handle, a.data.ptr, b.data.ptr)
with plan:
    c = cp.fft.fft(a) 
assert cp.allclose(b, c)
