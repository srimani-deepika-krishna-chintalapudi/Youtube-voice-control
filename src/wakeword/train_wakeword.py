"""
Hey YouTube — Wake-Word Model Trainer
Generates synthetic 16kHz speech dataset, extracts openWakeWord embeddings,
trains a neural classifier, and exports the calibrated models/hey_youtube.onnx.
"""
import os
import sys
import subprocess
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wavfile
from scipy import signal
from sklearn.neural_network import MLPClassifier
import onnx
from onnx import helper, TensorProto

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from openwakeword.utils import AudioFeatures
from src.config import MODELS_DIR, SAMPLE_RATE

DATA_DIR = BASE_DIR / "models" / "training_data"
PS_SCRIPT = BASE_DIR / "src" / "wakeword" / "generate_samples.ps1"


def generate_audio_dataset():
    """Generates synthetic positive and negative audio samples using offline SAPI."""
    pos_dir = DATA_DIR / "positive"
    neg_dir = DATA_DIR / "negative"
    os.makedirs(pos_dir, exist_ok=True)
    os.makedirs(neg_dir, exist_ok=True)

    print("\n[1] Synthesizing acoustic training samples...")

    # Positive Phrases ("Hey YouTube" variations)
    pos_phrases = [
        "Hey YouTube",
        "Hey You Tube",
        "hey youtube",
        "hey youtube.",
        "Hey YouTube!",
        "A YouTube",
    ]

    # Negative Phrases (Confusers, normal speech, crochet phrases)
    neg_phrases = [
        "Hey Siri",
        "Hey Google",
        "Alexa",
        "Hey",
        "YouTube",
        "crochet tutorial",
        "single crochet stitch",
        "yarn over and pull through",
        "pause the video please",
        "skip this part",
        "hello there",
        "can you hear me",
        "play next track",
        "fast forward ten seconds",
        "turn the volume up",
        "knit two together",
        "magic ring tutorial",
    ]

    # Generate Positives with different speech rates (-3 to +4)
    pos_files = []
    idx = 0
    for phrase in pos_phrases:
        for rate in range(-3, 5):
            out_file = pos_dir / f"pos_{idx}.wav"
            subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass",
                "-File", str(PS_SCRIPT), str(out_file), phrase, str(rate)
            ], capture_output=True)
            if out_file.exists():
                pos_files.append(out_file)
                idx += 1

    # Generate Negatives
    neg_files = []
    idx = 0
    for phrase in neg_phrases:
        for rate in [-2, 0, 2]:
            out_file = neg_dir / f"neg_{idx}.wav"
            subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass",
                "-File", str(PS_SCRIPT), str(out_file), phrase, str(rate)
            ], capture_output=True)
            if out_file.exists():
                neg_files.append(out_file)
                idx += 1

    print(f"[OK] Generated {len(pos_files)} positive samples and {len(neg_files)} negative samples.")
    return pos_files, neg_files


def load_and_resample(wav_path: Path, target_sr: int = 16000) -> np.ndarray:
    """Reads a WAV file, converts to mono, and resamples to target_sr."""
    sr, data = wavfile.read(str(wav_path))
    if data.ndim > 1:
        data = data.mean(axis=1)

    if sr != target_sr:
        num_samples = int(len(data) * target_sr / sr)
        data = signal.resample(data, num_samples)

    # Normalize to int16 range
    data = np.clip(data, -32768, 32767).astype(np.int16)
    return data


def extract_features(audio_files, af: AudioFeatures, is_positive: bool = True):
    """Feeds audio files into AudioFeatures to get (16, 96) feature embeddings."""
    X = []
    y = []

    for wav_file in audio_files:
        try:
            audio = load_and_resample(wav_file)
            # Pad audio to at least 1.5 seconds (24000 samples)
            if len(audio) < 24000:
                pad_len = 24000 - len(audio)
                audio = np.pad(audio, (0, pad_len), mode="constant")

            # Stream audio through AudioFeatures in 80ms (1280 samples) chunks
            af.reset()
            chunk_size = 1280
            for i in range(0, len(audio) - chunk_size, chunk_size):
                chunk = audio[i : i + chunk_size]
                af(chunk)
                feats = af.get_features(16)
                if feats.shape == (1, 16, 96):
                    # Flatten to 1536 vector
                    flat_feat = feats.reshape(1, -1)[0]
                    X.append(flat_feat)
                    y.append(1 if is_positive else 0)
        except Exception as e:
            print(f"Error processing {wav_file}: {e}")

    return X, y


def train_and_export_onnx():
    pos_files, neg_files = generate_audio_dataset()

    print("\n[2] Extracting openWakeWord embedding features...")
    af = AudioFeatures()

    X_pos, y_pos = extract_features(pos_files, af, is_positive=True)
    X_neg, y_neg = extract_features(neg_files, af, is_positive=False)

    # Add synthetic noise and silence negative samples
    for _ in range(50):
        noise = np.random.normal(0, 500, 24000).astype(np.int16)
        af.reset()
        for i in range(0, len(noise) - 1280, 1280):
            af(noise[i : i + 1280])
            feats = af.get_features(16)
            if feats.shape == (1, 16, 96):
                X_neg.append(feats.reshape(1, -1)[0])
                y_neg.append(0)

    X = np.array(X_pos + X_neg, dtype=np.float32)
    y = np.array(y_pos + y_neg, dtype=np.int32)
    print(f"[OK] Total feature samples: {len(X)} (Positives: {len(X_pos)}, Negatives: {len(X_neg)})")

    # Train Neural Network Classifier
    print("\n[3] Training neural wake-word classifier...")
    clf = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        max_iter=300,
        random_state=42,
        alpha=0.01,
    )
    clf.fit(X, y)
    train_acc = clf.score(X, y)
    print(f"[OK] Classifier trained with accuracy: {train_acc * 100:.2f}%")

    # Extract weights & biases from trained MLP
    w1, w2, w3 = clf.coefs_
    b1, b2, b3 = clf.intercepts_

    # Export to ONNX
    print("\n[4] Exporting to models/hey_youtube.onnx...")
    input_dim = 1536
    h1_dim = 64
    h2_dim = 32
    out_dim = 1

    input_tensor = helper.make_tensor_value_info("onnx::Flatten_0", TensorProto.FLOAT, [1, 16, 96])
    output_tensor = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 1])

    w1_init = helper.make_tensor("w1", TensorProto.FLOAT, [input_dim, h1_dim], w1.astype(np.float32).flatten())
    b1_init = helper.make_tensor("b1", TensorProto.FLOAT, [h1_dim], b1.astype(np.float32).flatten())

    w2_init = helper.make_tensor("w2", TensorProto.FLOAT, [h1_dim, h2_dim], w2.astype(np.float32).flatten())
    b2_init = helper.make_tensor("b2", TensorProto.FLOAT, [h2_dim], b2.astype(np.float32).flatten())

    w3_init = helper.make_tensor("w3", TensorProto.FLOAT, [h2_dim, out_dim], w3.astype(np.float32).flatten())
    b3_init = helper.make_tensor("b3", TensorProto.FLOAT, [out_dim], b3.astype(np.float32).flatten())

    flatten_node = helper.make_node("Flatten", ["onnx::Flatten_0"], ["flat"], axis=1)
    matmul1_node = helper.make_node("MatMul", ["flat", "w1"], ["dense1"])
    add1_node = helper.make_node("Add", ["dense1", "b1"], ["dense1_bias"])
    relu1_node = helper.make_node("Relu", ["dense1_bias"], ["relu1"])

    matmul2_node = helper.make_node("MatMul", ["relu1", "w2"], ["dense2"])
    add2_node = helper.make_node("Add", ["dense2", "b2"], ["dense2_bias"])
    relu2_node = helper.make_node("Relu", ["dense2_bias"], ["relu2"])

    matmul3_node = helper.make_node("MatMul", ["relu2", "w3"], ["dense3"])
    add3_node = helper.make_node("Add", ["dense3", "b3"], ["dense3_bias"])
    sigmoid_node = helper.make_node("Sigmoid", ["dense3_bias"], ["output"])

    graph = helper.make_graph(
        nodes=[
            flatten_node, matmul1_node, add1_node, relu1_node,
            matmul2_node, add2_node, relu2_node,
            matmul3_node, add3_node, sigmoid_node
        ],
        name="hey_youtube_trained_wakeword",
        inputs=[input_tensor],
        outputs=[output_tensor],
        initializer=[w1_init, b1_init, w2_init, b2_init, w3_init, b3_init]
    )

    model = helper.make_model(graph, producer_name="hey_youtube_trainer", opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    output_path = MODELS_DIR / "hey_youtube.onnx"
    onnx.save(model, str(output_path))
    print(f"[OK] Successfully saved trained 'Hey YouTube' ONNX model to:\n     {output_path}")


if __name__ == "__main__":
    train_and_export_onnx()
