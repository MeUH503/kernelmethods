
import numpy as np
from numbers import Number
from pytest import raises, warns
from hypothesis import given, strategies, unlimited
from hypothesis import settings as hyp_settings
from hypothesis import HealthCheck
from kernelmethods.numeric_kernels import PolyKernel, GaussianKernel, LinearKernel, \
    LaplacianKernel
from kernelmethods.utils import check_callable
from kernelmethods.base import KernelMatrix, KernelFromCallable, BaseKernelFunction
from kernelmethods.operations import is_positive_semidefinite

default_feature_dim = 10
range_feature_dim = [10, 50]
range_num_samples = [50, 100]

range_polynomial_degree = [2, 10] # degree=1 is tested in LinearKernel()

np.random.seed(42)

# choosing skip_input_checks=False will speed up test runs
# default values for parameters
SupportedKernels = (GaussianKernel(), PolyKernel(), LinearKernel(),
                    LaplacianKernel())
num_tests_psd_kernel = 3

def gen_random_array(dim):
    """To better control precision and type of floats"""

    # TODO input sparse arrays for test
    return np.random.rand(dim)

def gen_random_sample(num_samples, sample_dim):
    """To better control precision and type of floats"""

    # TODO input sparse arrays for test
    return np.random.rand(num_samples, sample_dim)


def _test_for_all_kernels(kernel, sample_dim):
    """Common tests that all kernels must pass."""

    x = gen_random_array(sample_dim)
    y = gen_random_array(sample_dim)

    try:
        result = kernel(x, y)
    except Exception:
        raise RuntimeError('{} unable to calculate!\n'
                           ' on x {}\n y{}'.format(kernel, x, y))

    if not isinstance(result, Number):
        raise ValueError('result {} of type {} is not a number!\n'
                         'x={}\ny={}\nkernel={}\n'
                         ''.format(result, type(result), x, y, kernel))

    if kernel(y, x) != result:
        raise ValueError('{} is not symmetric!'
                         'x={}\n y={}\n kernel={}\n'
                         ''.format(kernel.name, x, y, kernel))

    # ensuring it produces a PSD KM
    kernel.is_psd()


def test_kernel_design():
    """
    Every kernel must be
    1. must have a name defined
    2. must be callable with two samples
    3. returns a number

    """

    for kernel in SupportedKernels:

        # must be callable with 2 args
        check_callable(kernel, min_num_args=2)

        if not hasattr(kernel, 'name'):
            raise TypeError('{} does not have name attribute!'.format(kernel))

        # only numeric data is accepted and other dtypes must raise an error
        for non_num in ['string',
                        (True, False, True),
                        [object, object] ]:
            with raises(ValueError):
                _ = kernel(non_num, non_num)


def _test_func_is_valid_kernel(kernel, sample_dim, num_samples):
    """A func is a valid kernel if the kernel matrix generated by it is PSD.

    Not including this in tests for all kernels to allow for non-PSD kernels in the future

    """

    KM = KernelMatrix(kernel, name='TestKM')
    KM.attach_to(gen_random_sample(num_samples, sample_dim))
    is_psd = is_positive_semidefinite(KM.full, verbose=True)
    if not is_psd:
        raise ValueError('{} is not PSD'.format(str(KM)))


@hyp_settings(max_examples=num_tests_psd_kernel, deadline=None,
              timeout=unlimited, suppress_health_check=HealthCheck.all())
@given(strategies.integers(range_feature_dim[0], range_feature_dim[1]),
       strategies.integers(range_num_samples[0], range_num_samples[1]),
       strategies.integers(range_polynomial_degree[0], range_polynomial_degree[1]),
       strategies.floats(min_value=0, max_value=1e3,
                         allow_nan=False, allow_infinity=False))
def test_polynomial_kernel(sample_dim, num_samples,
                           poly_degree, poly_intercept):
    """Tests specific for Polynomial kernel."""

    poly = PolyKernel(degree=poly_degree, b=poly_intercept, skip_input_checks=False)
    _test_for_all_kernels(poly, sample_dim)
    _test_func_is_valid_kernel(poly, sample_dim, num_samples)


@hyp_settings(max_examples=num_tests_psd_kernel, deadline=None,
              timeout=unlimited, suppress_health_check=HealthCheck.all())
@given(strategies.integers(range_feature_dim[0], range_feature_dim[1]),
       strategies.integers(range_num_samples[0], range_num_samples[1]),
       strategies.floats(min_value=0, max_value=1e6,
                         allow_nan=False, allow_infinity=False))
def test_gaussian_kernel(sample_dim, num_samples, sigma):
    """Tests specific for Polynomial kernel."""

    gaussian = GaussianKernel(sigma=sigma, skip_input_checks=False)
    _test_for_all_kernels(gaussian, sample_dim)
    _test_func_is_valid_kernel(gaussian, sample_dim, num_samples)

@hyp_settings(max_examples=num_tests_psd_kernel, deadline=None,
              timeout=unlimited, suppress_health_check=HealthCheck.all())
@given(strategies.integers(range_feature_dim[0], range_feature_dim[1]),
       strategies.integers(range_num_samples[0], range_num_samples[1]))
def test_linear_kernel(sample_dim, num_samples):
    """Tests specific for Polynomial kernel."""

    linear = LinearKernel(skip_input_checks=False)
    _test_for_all_kernels(linear, sample_dim)
    _test_func_is_valid_kernel(linear, sample_dim, num_samples)


@hyp_settings(max_examples=num_tests_psd_kernel, deadline=None,
              timeout=unlimited, suppress_health_check=HealthCheck.all())
@given(strategies.integers(range_feature_dim[0], range_feature_dim[1]),
       strategies.integers(range_num_samples[0], range_num_samples[1]),
       strategies.floats(min_value=0, max_value=1e6,
                         allow_nan=False, allow_infinity=False))
def test_laplacian_kernel(sample_dim, num_samples, gamma):
    """Tests specific for Polynomial kernel."""

    laplacian = LaplacianKernel(gamma=gamma, skip_input_checks=False)
    _test_for_all_kernels(laplacian, sample_dim)
    _test_func_is_valid_kernel(laplacian, sample_dim, num_samples)
