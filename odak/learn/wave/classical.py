from odak import np
import torch, torch.fft
from .toolkit import fftshift, ifftshift
from .__init__ import set_amplitude

def propagate_beam(field,k,distance,dx,wavelength,propagation_type='IR Fresnel'):
    """
    Definitions for Fresnel impulse respone (IR), Fresnel Transfer Function (TF), Fraunhofer diffraction in accordence with "Computational Fourier Optics" by David Vuelz.

    Parameters
    ==========
    field            : torch.complex128
                       Complex field (MxN).
    k                : odak.wave.wavenumber
                       Wave number of a wave, see odak.wave.wavenumber for more.
    distance         : float
                       Propagation distance.
    dx               : float
                       Size of one single pixel in the field grid (in meters).
    wavelength       : float
                       Wavelength of the electric field.
    propagation_type : str
                       Type of the propagation (IR Fresnel, TR Fresnel, Fraunhofer).

    Returns
    =======
    result           : torch.complex128
                       Final complex field (MxN).
    """
    nv, nu = field.shape[-2], field.shape[-1]
    x      = torch.linspace(-nv*dx,nv*dx,nv)
    y      = torch.linspace(-nu*dx,nu*dx,nu)
    X,Y    = torch.meshgrid(x,y)
    k      = torch.tensor(k, dtype=field.dtype)
    Z      = X**2+Y**2
    if propagation_type == 'IR Fresnel':
       h      = 1./(1j*wavelength*distance)*torch.exp(1j*k*0.5/distance*Z)
       h      = torch.fft.fftn(fftshift(h))*pow(dx,2)
       h      = h.to(field.device)
       U1     = torch.fft.fftn(fftshift(field))
       U2     = h*U1
       result = ifftshift(torch.fft.ifftn(U2))
    elif propagation_type == 'Bandlimited Angular Spectrum':
       h         = 1./(1j*wavelength*distance)*torch.exp(1j*k*(0.5 / distance * Z))
       h         = torch.fft.fftn(fftshift(h)) * pow(dx, 2)
       h         = h.to(field.device)
       flimx     = int(1/(((2*distance*(1./(nv)))**2+1)**0.5*wavelength))
       flimy     = int(1/(((2*distance*(1./(nu)))**2+1)**0.5*wavelength))
       mask      = torch.zeros((nu,nv), dtype=torch.cfloat)
       mask[...] = torch.logical_and(torch.lt(torch.abs(X), flimx), torch.lt(torch.abs(Y), flimy))
       mask      = mask.to(field.device)
       mask      = set_amplitude(h, mask)
       U1        = torch.fft.fftn(fftshift(field))
       U2        = mask * U1 
       result    = ifftshift(torch.fft.ifftn(U2))
    elif propagation_type == 'TR Fresnel':
       h      = torch.exp(1j*k*distance)*torch.exp(-1j*np.pi*wavelength*distance*Z)
       h      = fftshift(h)
       h      = h.to(field.device)
       U1     = torch.fft.fftn(fftshift(field))
       U2     = h*U1
       result = ifftshift(torch.fft.ifftn(U2))
    elif propagation_type == 'Fraunhofer':
       c      = 1./(1j*wavelength*distance)*torch.exp(1j*k*0.5/distance*Z)
       c      = c.to(field.device)
       result = c*ifftshift(torch.fft.fftn(fftshift(field)))*pow(dx,2)
    return result
