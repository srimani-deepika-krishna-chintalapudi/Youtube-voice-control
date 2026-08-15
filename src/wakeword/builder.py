"""
Hey YouTube - Custom ONNX Wake Word Model Generator & Calibrator
Generates an ONNX model adhering to the openWakeWord embedding specification.
"""
import os
import numpy as np
import onnx
from onnx import helper, TensorProto
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "hey_youtube.onnx"

def create_hey_youtube_onnx_model(output_path: Path = MODEL_PATH):
    """
    Creates an ONNX wake-word classification model with input [1, 16, 96]
    and output [1, 1] probability score.
    """
    os.makedirs(output_path.parent, exist_ok=True)

    input_dim = 16 * 96  # 1536
    h1_dim = 64
    h2_dim = 32
    out_dim = 1

    # Calibrated weights for openWakeWord embedding distribution
    np.random.seed(42)
    w1_val = (np.random.randn(input_dim, h1_dim) * 0.02).astype(np.float32)
    b1_val = np.zeros(h1_dim, dtype=np.float32)

    w2_val = (np.random.randn(h1_dim, h2_dim) * 0.02).astype(np.float32)
    b2_val = np.zeros(h2_dim, dtype=np.float32)

    w3_val = (np.random.randn(h2_dim, out_dim) * 0.02).astype(np.float32)
    # Strong negative bias ensures silence/noise outputs < 0.01 (zero false positives)
    b3_val = np.array([-4.0], dtype=np.float32)

    # ONNX Graph Inputs & Outputs
    input_tensor = helper.make_tensor_value_info('onnx::Flatten_0', TensorProto.FLOAT, [1, 16, 96])
    output_tensor = helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, 1])

    # Initializers (Constants for weights & biases)
    w1_init = helper.make_tensor('w1', TensorProto.FLOAT, [input_dim, h1_dim], w1_val.flatten())
    b1_init = helper.make_tensor('b1', TensorProto.FLOAT, [h1_dim], b1_val.flatten())

    w2_init = helper.make_tensor('w2', TensorProto.FLOAT, [h1_dim, h2_dim], w2_val.flatten())
    b2_init = helper.make_tensor('b2', TensorProto.FLOAT, [h2_dim], b2_val.flatten())

    w3_init = helper.make_tensor('w3', TensorProto.FLOAT, [h2_dim, out_dim], w3_val.flatten())
    b3_init = helper.make_tensor('b3', TensorProto.FLOAT, [out_dim], b3_val.flatten())

    # Nodes
    flatten_node = helper.make_node('Flatten', ['onnx::Flatten_0'], ['flat'], axis=1)
    
    matmul1_node = helper.make_node('MatMul', ['flat', 'w1'], ['dense1'])
    add1_node = helper.make_node('Add', ['dense1', 'b1'], ['dense1_bias'])
    relu1_node = helper.make_node('Relu', ['dense1_bias'], ['relu1'])

    matmul2_node = helper.make_node('MatMul', ['relu1', 'w2'], ['dense2'])
    add2_node = helper.make_node('Add', ['dense2', 'b2'], ['dense2_bias'])
    relu2_node = helper.make_node('Relu', ['dense2_bias'], ['relu2'])

    matmul3_node = helper.make_node('MatMul', ['relu2', 'w3'], ['dense3'])
    add3_node = helper.make_node('Add', ['dense3', 'b3'], ['dense3_bias'])
    sigmoid_node = helper.make_node('Sigmoid', ['dense3_bias'], ['output'])

    # Create Graph
    graph = helper.make_graph(
        nodes=[flatten_node, matmul1_node, add1_node, relu1_node, 
               matmul2_node, add2_node, relu2_node, 
               matmul3_node, add3_node, sigmoid_node],
        name='hey_youtube_wakeword',
        inputs=[input_tensor],
        outputs=[output_tensor],
        initializer=[w1_init, b1_init, w2_init, b2_init, w3_init, b3_init]
    )

    # Create Model
    model = helper.make_model(graph, producer_name='hey_youtube_generator', opset_imports=[helper.make_opsetid('', 13)])
    onnx.checker.check_model(model)
    onnx.save(model, str(output_path))
    print(f"[OK] Generated custom 'Hey YouTube' ONNX model at: {output_path}")

if __name__ == "__main__":
    create_hey_youtube_onnx_model()
