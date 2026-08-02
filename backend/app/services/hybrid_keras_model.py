import os
import logging
import numpy as np
from typing import Dict, Any, Tuple

logger = logging.getLogger("finswarm.hybrid_keras_model")

MODEL_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "finswarm_keras_model.h5")

class HybridKerasPredictionModel:
    """
    HybridKerasPredictionModel
    Implements a 6-Step TensorFlow (Keras API) Late Fusion Neural Network:
    - Input 1: 120-Day Daily OHLCV Time-Series (120, 5) passed to an LSTM(64) layer.
    - Input 2: 14-Agent Swarm Sentiment Vector (14,) passed to a Dense(16) layer.
    - Feature Concatenation (Late Fusion) -> Dense(32, ReLU) -> Dense(1, Linear).
    - Loss: MSE, Optimizer: Adam.
    """
    def __init__(self):
        self.model = None
        self.scaler_price = None
        self.scaler_sentiment = None
        self._init_or_load_model()

    def _build_model(self):
        """Step 3 & 4: Build Keras Functional API Architecture and Compile."""
        try:
            import tensorflow as tf
            from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate, Dropout
            from tensorflow.keras.models import Model
            
            # 1. Historical Chart Branch (120 days x 5 features)
            chart_input = Input(shape=(120, 5), name="chart_input")
            lstm_out = LSTM(64, return_sequences=False)(chart_input)
            
            # 2. Swarm Sentiment Branch (14 agent sentiment scores)
            sentiment_input = Input(shape=(14,), name="sentiment_input")
            sentiment_dense = Dense(16, activation="relu")(sentiment_input)
            
            # 3. Feature Fusion Concatenation
            merged = Concatenate()([lstm_out, sentiment_dense])
            dense_boss = Dense(32, activation="relu")(merged)
            dense_boss = Dropout(0.2)(dense_boss)
            
            # 4. Output Layer: Next-day percentage return forecast
            output_prediction = Dense(1, activation="linear", name="price_return_pred")(dense_boss)
            
            model = Model(inputs=[chart_input, sentiment_input], outputs=output_prediction)
            model.compile(optimizer="adam", loss="mse", metrics=["mae"])
            return model
        except Exception as e:
            logger.warning(f"TensorFlow Keras build fallback ({e}). Using numerical fallback.")
            return None

    def _init_or_load_model(self):
        """Initializes or loads existing Keras model weights."""
        self.model = self._build_model()
        if self.model and os.path.exists(MODEL_WEIGHTS_PATH):
            try:
                self.model.load_weights(MODEL_WEIGHTS_PATH)
                logger.info(f"Loaded trained Keras weights from {MODEL_WEIGHTS_PATH}")
            except Exception as e:
                logger.warning(f"Could not load Keras weights ({e}). Model initialized with fresh weights.")

    def fit_model(self, X_charts: np.ndarray, X_sentiments: np.ndarray, y_returns: np.ndarray, epochs: int = 50, batch_size: int = 32) -> Dict[str, Any]:
        """
        Step 5: Train the model on training tensors using .fit() loop.
        - X_charts: (N, 120, 5)
        - X_sentiments: (N, 14)
        - y_returns: (N, 1)
        """
        if self.model is None:
            return {"status": "error", "message": "Keras model not compiled (TensorFlow unavailable)."}

        logger.info(f"Starting Keras training loop over {epochs} epochs (batch_size={batch_size})...")
        history = self.model.fit(
            x=[X_charts, X_sentiments],
            y=y_returns,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0
        )
        
        # Save trained weights
        try:
            self.model.save_weights(MODEL_WEIGHTS_PATH)
            logger.info(f"Saved trained weights to {MODEL_WEIGHTS_PATH}")
        except Exception as e:
            logger.warning(f"Could not save weights: {e}")

        final_loss = float(history.history['loss'][-1])
        final_mae = float(history.history.get('mae', [0.0])[-1])
        logger.info(f"Training complete. Final Loss (MSE): {final_loss:.6f}, MAE: {final_mae:.6f}")
        return {"status": "success", "final_loss": final_loss, "final_mae": final_mae}

    def predict_price_delta(self, ohlcv_120d: np.ndarray, sentiment_vector_14: np.ndarray, current_price: float) -> Dict[str, Any]:
        """
        Step 6: Inference Test.
        Predicts next-day stock price and 30-day forecast trajectory.
        """
        # Ensure correct array shapes
        if ohlcv_120d.ndim == 2:
            ohlcv_120d = np.expand_dims(ohlcv_120d, axis=0) # (1, 120, 5)
        if sentiment_vector_14.ndim == 1:
            sentiment_vector_14 = np.expand_dims(sentiment_vector_14, axis=0) # (1, 14)

        if self.model is not None:
            try:
                predicted_return = float(self.model.predict([ohlcv_120d, sentiment_vector_14], verbose=0)[0][0])
            except Exception as e:
                logger.warning(f"Inference error ({e}). Using mathematical fallback.")
                predicted_return = self._fallback_prediction_math(sentiment_vector_14)
        else:
            predicted_return = self._fallback_prediction_math(sentiment_vector_14)

        # Calculate projected next day price
        next_day_price = round(current_price * (1.0 + predicted_return), 2)
        
        # Generate 30-day forecast trajectory with exponential sentiment decay S(t) = S0 * exp(-lambda * t)
        trajectory = []
        decay_rate = 0.08
        running_price = current_price
        for day in range(1, 31):
            daily_shock = predicted_return * np.exp(-decay_rate * day)
            # Add stochastic drift
            noise = np.random.normal(0, 0.003)
            running_price *= (1.0 + daily_shock + noise)
            trajectory.append(round(running_price, 2))

        return {
            "current_price": current_price,
            "predicted_next_day_price": next_day_price,
            "predicted_return_pct": round(predicted_return * 100, 2),
            "forecast_30d_trajectory": trajectory
        }

    def _fallback_prediction_math(self, sentiment_vector_14: np.ndarray) -> float:
        """Deterministic mathematical fallback when Keras weights are uninitialized."""
        mean_sentiment = float(np.mean(sentiment_vector_14))
        # Map sentiment [-1.0, 1.0] to return [-5%, +5%]
        return mean_sentiment * 0.05
