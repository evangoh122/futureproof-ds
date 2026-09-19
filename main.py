"""Run the trial-conversion data and model-training pipeline."""

import logging
from trial_conversion.etl.bronze import extract_raw_data
from trial_conversion.etl.silver import clean_data
from trial_conversion.feature_engineering.features import add_features
from trial_conversion.modeling.train import train_model

# Config Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def run_pipeline(*, bronze_step, silver_step, feature_step, train_step):
    """Run each pipeline stage and return the trained model."""
    logger.info("Starting Bronze stage")
    bronze_step()
    logger.info("Starting Silver stage")
    cleaned_data = silver_step()
    logger.info("Starting feature-engineering stage")
    featured_data = feature_step(cleaned_data)
    logger.info("Starting model-training stage")
    return train_step(featured_data)


def main():
    return run_pipeline(
        bronze_step=extract_raw_data,
        silver_step=clean_data,
        feature_step=add_features,
        train_step=train_model,
      )


if __name__ == "__main__":
    main()
