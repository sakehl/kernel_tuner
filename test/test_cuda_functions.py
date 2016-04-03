import numpy
from nose import SkipTest
from nose.tools import nottest, raises
from .context import kernel_tuner
from .context import cuda

try:
    import pycuda.driver
except Exception:
    pass

@nottest
def skip_if_no_cuda_device():
    try:
        from pycuda.autoinit import context
    #except pycuda.driver.RuntimeError, e:
    except Exception, e:
        if "No module named pycuda.autoinit" in str(e):
            raise SkipTest("PyCuda not installed")
        elif "no CUDA-capable device is detected" in str(e):
            raise SkipTest("no CUDA-capable device is detected")
        else:
            raise e

def test_create_gpu_args():

    skip_if_no_cuda_device()

    size = 1000
    a = numpy.int32(75)
    b = numpy.random.randn(size).astype(numpy.float32)
    c = numpy.zeros_like(b)

    arguments = [c, a, b]

    dev = cuda.CudaFunctions(0)
    gpu_args = dev.create_gpu_args(arguments)

    assert isinstance(gpu_args[0], pycuda.driver.DeviceAllocation)
    assert isinstance(gpu_args[1], numpy.int32)
    assert isinstance(gpu_args[2], pycuda.driver.DeviceAllocation)

    gpu_args[0].free()
    gpu_args[2].free()


def test_compile():

    skip_if_no_cuda_device()

    original_kernel = """
    __global__ void vector_add(float *c, float *a, float *b, int n) {
        __shared__ float test[shared_size];
        int i = blockIdx.x * blockDim.x + threadIdx.x;
        if (i<n) {
            test[0] = a[i];
            c[i] = test[0] + b[i];
        }
    }
    """

    kernel_string = original_kernel.replace("shared_size", str(100*1024*1024))

    dev = cuda.CudaFunctions(0)
    try:
        func = dev.compile("vector_add", kernel_string)
        assert False
    except Exception, e:
        if "uses too much shared data" in str(e):
            assert True
        else:
            assert False

    kernel_string = original_kernel.replace("shared_size", str(100))
    try:
        func = dev.compile("vector_add", kernel_string)
        assert True
    except Exception:
        assert False