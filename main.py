"""Run the trial-conversion data and model-training pipeline."""

import logging
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# Config Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

PROJECT_ROOT = Path(__file__).resolve().parent


def load_module(module_name, module_path):
    """Load a pipeline module from its existing file-system location."""
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load pipeline module from {module_path}.")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_step(module, *, function_name, module_path, expected_signature):
    """Return a pipeline callable or explain the interface it must expose."""
    step = getattr(module, function_name, None)
    if not callable(step):
        raise RuntimeError(
            f"{module_path} must define {expected_signature} "
            "before the pipeline can run."
        )
    return step


def run_pipeline(*, bronze_step, silver_step, feature_step, train_step):
    """Run each pipeline stage and return the trained model."""
    bronze_step()
    cleaned_data = silver_step()
    featured_data = feature_step(cleaned_data)
    return train_step(featured_data)


def main():
    """Load and run the Bronze, Silver, feature, and training stages."""
    stage_definitions = (
        (
            "pipeline_bronze",
            PROJECT_ROOT / "src" / "ETL" / "Bronze.py",
            "extract_raw_data",
            "extract_raw_data()",
        ),
        (
            "pipeline_silver",
            PROJECT_ROOT / "src" / "ETL" / "Silver.py",
            "clean_data",
            "clean_data()",
        ),
        (
            "pipeline_features",
            PROJECT_ROOT / "src" / "Feature Engineering" / "features.py",
            "add_features",
            "add_features(cleaned_data)",
        ),
        (
            "pipeline_train",
            PROJECT_ROOT / "src" / "Modeling" / "train.py",
            "train_model",
            "train_model(featured_data)",
        ),
    )

    steps = []
    for module_name, module_path, function_name, expected_signature in stage_definitions:
        module = load_module(module_name, module_path)
        relative_path = module_path.relative_to(PROJECT_ROOT).as_posix()
        steps.append(
            require_step(
                module,
                function_name=function_name,
                module_path=relative_path,
                expected_signature=expected_signature,
            )
        )

    return run_pipeline(
        bronze_step=steps[0],
        silver_step=steps[1],
        feature_step=steps[2],
        train_step=steps[3],
    )


if __name__ == "__main__":
    main()
