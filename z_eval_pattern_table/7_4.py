# To construct a pattern table and corresponding seq impact
import os
import numpy as np
import tvm
from tvm import relay
from tvm.relay import transform
from Autotuning.util import viz2file, simu_mem_from_relay

root = '/home/nie/RelayOpt/eval/pattern_table/'

'''
Construct pattern
'''
dtype = "uint8"
shape_x = [1, 4, 24, 24]
shape_w = [8, 4, 1, 1]
x = relay.var("x", shape=shape_x, dtype=dtype)
w = relay.var("w", shape=shape_w, dtype=dtype)
zero = relay.const(0)
one = relay.const(1.0)

# Tested expression.
op0 = relay.qnn.op.dequantize(x, relay.const(0.64), relay.const(2))
op0 = relay.transpose(op0, axes=[0, 1, 2, 3])
op1 = relay.op.nn.avg_pool2d(op0, [3, 3])
op2 = relay.qnn.op.dequantize(w, relay.const(0.5), relay.const(10))
op3 = relay.op.nn.conv2d(op1, op2, kernel_size=[1, 1])
op = relay.qnn.op.quantize(op3, one, zero, out_dtype="uint8")


before = tvm.IRModule.from_expr(op)
before = transform.InferType()(before)
print(before)

'''
For test: load mod from file
'''
# file_path  = os.path.join(root, 'test/code.txt')
# with open(file_path, 'r') as f:
#     before = relay.parse(f.read())
# before = transform.DynamicToStatic()(before)

'''
Visualize
'''
case_dir = os.path.join(root, '7_4')
os.system(f'rm -rf {case_dir}')
os.mkdir(case_dir)
case_path = os.path.join(case_dir, 'code.txt')
with open(case_path, 'w') as f:
    f.write(before.astext())
viz2file(case_path)

'''
Origin memory
'''
before = transform.InferType()(before)
origin_mem = simu_mem_from_relay(before)
print('Origin:', origin_mem, 'mem')

'''
Optimized memory
'''
default = before
default = transform.SimplifyExpr()(default)
default = transform.FuseOps(4)(default)
default_mem = simu_mem_from_relay(default)

opass = before
opass = transform.SimplifyExpr()(opass)
opass = transform.FakeQuantizationToInteger()(opass)
opass = transform.FuseOps(4)(opass)
opass_mem = simu_mem_from_relay(opass)

ref = before
ref = transform.SimplifyExpr()(ref)
ref = transform.FuseOps(4)(ref)
ref = transform.FakeQuantizationToInteger()(ref)
ref_mem = simu_mem_from_relay(ref)

print('Default:', default_mem, 'mem;', (origin_mem-default_mem)/origin_mem)
print('OPass:', opass_mem, 'mem;', (origin_mem-opass_mem)/origin_mem)
print('OPass:', ref_mem, 'mem;', (origin_mem-ref_mem)/origin_mem)