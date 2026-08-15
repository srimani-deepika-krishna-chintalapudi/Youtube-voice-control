"""
Phase 4: Wake-Word Evaluation Suite
Evaluates Wake-Word detection accuracy, false positive rejection, and latency metrics.
"""
import sys
import time
import argparse
from pathlib import Path
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.wakeword.engine import WakeWordEngine
from src.audio.recorder import AudioRecorder
from src.config import CHUNK_SIZE, SAMPLE_RATE

class WakeWordEvaluator:
    """
    Automated and interactive evaluation harness for 'Hey YouTube' wake word detection.
    """

    def __init__(self, threshold: float = 0.5):
        self.engine = WakeWordEngine(threshold=threshold)
        self.recorder = AudioRecorder()
        self.results = {
            "positives_tested": 0,
            "positives_detected": 0,
            "confusers_tested": 0,
            "false_positives": 0,
            "background_chunks_tested": 0,
            "background_false_positives": 0,
            "latencies_ms": [],
        }

    def run_automated_stress_test(self, num_frames: int = 200):
        """
        Feeds synthetic audio frames (silence, Gaussian noise, frequency sweeps)
        to measure baseline false positives and latency distribution.
        """
        print("\n" + "=" * 60)
        print("RUNNING AUTOMATED STRESS & LATENCY TEST (200 frames)")
        print("=" * 60)

        latencies = []
        false_positives = 0

        for i in range(num_frames):
            # Mix silence, white noise, and simulated ambient noise
            if i % 3 == 0:
                chunk = np.zeros(CHUNK_SIZE, dtype=np.int16)
            elif i % 3 == 1:
                chunk = np.random.normal(0, 300, CHUNK_SIZE).astype(np.int16)
            else:
                # Simulated acoustic energy
                t = np.linspace(0, CHUNK_SIZE / SAMPLE_RATE, CHUNK_SIZE)
                chunk = (np.sin(2 * np.pi * 300 * t) * 500).astype(np.int16)

            t0 = time.perf_counter()
            detected, score = self.engine.is_wake_word_detected(chunk)
            t1 = time.perf_counter()

            latencies.append((t1 - t0) * 1000)
            if detected:
                false_positives += 1

        self.results["background_chunks_tested"] += num_frames
        self.results["background_false_positives"] += false_positives
        self.results["latencies_ms"].extend(latencies)

        avg_lat = np.mean(latencies)
        p95_lat = np.percentile(latencies, 95)
        print(f"[Results] Total Synthetic Frames Tested: {num_frames}")
        print(f"[Results] False Activations on Noise:   {false_positives} ({false_positives/num_frames*100:.1f}%)")
        print(f"[Results] Average Latency:              {avg_lat:.2f} ms")
        print(f"[Results] 95th Percentile Latency:      {p95_lat:.2f} ms")
        assert false_positives == 0, f"Unexpected false positives on noise: {false_positives}"
        print("[OK] Automated stress test passed: Zero false activations on noise.")

    def run_live_scenario(self, scenario_name: str, duration_sec: float, expected_triggers: int):
        """
        Records live microphone audio for duration_sec while user speaks test phrases.
        """
        print(f"\n--- Scenario: {scenario_name} ---")
        print(f"Duration: {duration_sec}s | Expected Triggers: {expected_triggers}")
        print("Get ready...")
        time.sleep(1.0)
        print(">>> START SPEAKING NOW <<<")

        self.recorder.start()
        start_time = time.time()
        trigger_count = 0
        max_score = 0.0

        while time.time() - start_time < duration_sec:
            chunk = self.recorder.get_chunk(timeout=0.2)
            if chunk is not None:
                t0 = time.perf_counter()
                detected, score = self.engine.is_wake_word_detected(chunk)
                t1 = time.perf_counter()
                self.results["latencies_ms"].append((t1 - t0) * 1000)

                if score > max_score:
                    max_score = score

                if detected:
                    trigger_count += 1
                    print(f"  [TRIGGER #{trigger_count}] Detected wake word! Score: {score:.3f}")

        self.recorder.stop()
        print(f">>> Scenario Complete. Detections: {trigger_count} (Max Score: {max_score:.3f})")
        return trigger_count

    def print_summary_report(self):
        """Prints a structured evaluation metrics table."""
        print("\n" + "=" * 60)
        print("       WAKE-WORD EVALUATION METRICS REPORT")
        print("=" * 60)
        print(f"Model Name:                  hey_youtube.onnx")
        print(f"Sensitivity Threshold:       {self.engine.threshold:.2f}")
        print(f"Cooldown Window:             {self.engine.cooldown_sec:.1f}s")
        print("-" * 60)
        if self.results["latencies_ms"]:
            print(f"Mean Inference Latency:      {np.mean(self.results['latencies_ms']):.2f} ms")
            print(f"Min Inference Latency:       {np.min(self.results['latencies_ms']):.2f} ms")
            print(f"Max Inference Latency:       {np.max(self.results['latencies_ms']):.2f} ms")
            print(f"P95 Inference Latency:       {np.percentile(self.results['latencies_ms'], 95):.2f} ms")
        print("-" * 60)
        print(f"Synthetic Background Frames: {self.results['background_chunks_tested']}")
        print(f"Background False Triggers:   {self.results['background_false_positives']}")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Wake-Word Evaluation Tool")
    parser.add_argument("--auto", action="store_true", help="Run automated benchmarks only")
    args = parser.parse_args()

    evaluator = WakeWordEvaluator()
    evaluator.run_automated_stress_test(num_frames=200)
    evaluator.print_summary_report()

if __name__ == "__main__":
    main()
