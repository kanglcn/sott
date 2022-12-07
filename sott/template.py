# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/template.ipynb.

# %% auto 0
__all__ = ['match_template', 'cu_match_template']

# %% ../nbs/template.ipynb 2
# The `_window_sum_2d`, `_cu_window_sum_2d`,`match_template` and `cu_match_template` are
# modified from the `_window_sum_2d` and `match_template` in `scikit-image` package.

# Copyright: 2009-2022 the scikit-image team
# License: BSD-3-Clause

# License: BSD-3-Clause

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
# .
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE HOLDERS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# %% ../nbs/template.ipynb 4
import numpy as np
from scipy.signal import fftconvolve
import cupy as cp
from cupyx.scipy.signal import fftconvolve as cu_fftconvolve
from typing import Union

# %% ../nbs/template.ipynb 5
def _window_sum_2d(image:np.ndarray, # reference image
                   window_shape:Union[list,tuple], # Two element list or tuple describe the shape of template image
                  ):

    window_sum = np.cumsum(image, axis=-2)
    window_sum = (window_sum[...,window_shape[0]:-1,:]
                  - window_sum[...,:-window_shape[0] - 1,:])

    window_sum = np.cumsum(window_sum, axis=-1)
    window_sum = (window_sum[..., window_shape[1]:-1]
                  - window_sum[..., :-window_shape[1] - 1])

    return window_sum

# %% ../nbs/template.ipynb 6
def _cu_window_sum_2d(image:cp.ndarray, # reference image(s) in cupy array
                      window_shape:Union[list,tuple], # Two element list or tuple describe the shape of template image
                     ):

    window_sum = cp.cumsum(image, axis=-2)
    window_sum = (window_sum[...,window_shape[0]:-1,:]
                  - window_sum[...,:-window_shape[0] - 1,:])

    window_sum = cp.cumsum(window_sum, axis=-1)
    window_sum = (window_sum[..., window_shape[1]:-1]
                  - window_sum[..., :-window_shape[1] - 1])

    return window_sum

# %% ../nbs/template.ipynb 7
def match_template(image:np.ndarray, # reference image(s)
                   template:np.ndarray, # template image(s)
                  ):
    template_shape = np.array(template.shape[-2:])
    image_shape = np.array(image.shape[-2:])

    pad_width = tuple((width, width) for width in template_shape)
    pad_width = ((0,0),)*(image.ndim-2)+pad_width
    image = np.pad(image, pad_width=pad_width, mode='constant')

    image_window_sum = _window_sum_2d(image, template_shape)
    image_window_sum2 = _window_sum_2d(image ** 2, template_shape)

    template_mean = np.expand_dims(template.mean(axis=(-2,-1)),axis=(-2,-1))
    template_volume = np.prod(template_shape) # scalar
    template_ssd = np.expand_dims(np.sum((template - template_mean) ** 2,axis=(-2,-1)),axis=(-2,-1))

    xcorr = fftconvolve(image, template[...,::-1, ::-1],
                            mode="valid",axes=(-2,-1))[...,1:-1, 1:-1]

    numerator = xcorr - image_window_sum * template_mean

    denominator = image_window_sum2
    np.multiply(image_window_sum, image_window_sum, out=image_window_sum)
    np.divide(image_window_sum, template_volume, out=image_window_sum)
    denominator -= image_window_sum
    denominator *= template_ssd
    np.maximum(denominator, 0, out=denominator)  # sqrt of negative number not allowed
    np.sqrt(denominator, out=denominator)

    response = np.zeros_like(xcorr, dtype=image.dtype)

    # avoid zero-division
    mask = denominator > np.finfo(image.dtype).eps

    response[mask] = numerator[mask] / denominator[mask]

    d0 = template_shape - 1
    d1 = d0 + image_shape - template_shape + 1

    return response[...,d0[0]:d1[0],d0[1]:d1[1]]

# %% ../nbs/template.ipynb 8
def cu_match_template(image:cp.ndarray, # reference image(s) in cupy array
                      template:cp.ndarray,# template image(s) in cupy array
                     ):
    template_shape = np.array(template.shape[-2:])
    image_shape = np.array(image.shape[-2:])

    pad_width = tuple((width, width) for width in template_shape)
    pad_width = ((0,0),)*(image.ndim-2)+pad_width
    image = cp.pad(image, pad_width=pad_width, mode='constant')

    image_window_sum = _window_sum_2d(image, template_shape)
    image_window_sum2 = _window_sum_2d(image ** 2, template_shape)

    template_mean = cp.expand_dims(template.mean(axis=(-2,-1)),axis=(-2,-1))
    template_volume = cp.prod(template_shape) # scalar
    template_ssd = cp.expand_dims(cp.sum((template - template_mean) ** 2,axis=(-2,-1)),axis=(-2,-1))

    xcorr = cu_fftconvolve(image, template[...,::-1, ::-1],
                            mode="valid",axes=(-2,-1))[...,1:-1, 1:-1]

    numerator = xcorr - image_window_sum * template_mean

    denominator = image_window_sum2
    cp.multiply(image_window_sum, image_window_sum, out=image_window_sum)
    cp.divide(image_window_sum, template_volume, out=image_window_sum)
    denominator -= image_window_sum
    denominator *= template_ssd
    cp.maximum(denominator, 0, out=denominator)  # sqrt of negative number not allowed
    cp.sqrt(denominator, out=denominator)

    response = cp.zeros_like(xcorr, dtype=image.dtype)

    # avoid zero-division
    mask = denominator > cp.finfo(image.dtype).eps

    response[mask] = numerator[mask] / denominator[mask]

    d0 = template_shape - 1
    d1 = d0 + image_shape - template_shape + 1

    return response[...,d0[0]:d1[0],d0[1]:d1[1]]