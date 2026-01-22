"""Train PyTorch LSTM for payment delay prediction."""

import logging
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

class PaymentDelayDataset(Dataset):
    """Dataset for payment delay sequences."""
    
    def __init__(self, sequences, targets):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class PaymentDelayLSTM(nn.Module):
    """LSTM model for payment delay prediction."""
    
    def __init__(self, input_size=4, hidden_size=64, num_layers=2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)
        # Take last timestep output
        last_output = lstm_out[:, -1, :]
        prediction = self.fc(last_output)
        return prediction


def generate_synthetic_sequences(n_sequences=1000, seq_length=10):
    """
    Generate synthetic payment history sequences.
    
    Features per timestep:
    - LC amount (normalized)
    - Days since issue
    - Discrepancy flag (0/1)
    - Port risk score (0-1)
    
    Target: Payment delay in days
    """
    np.random.seed(42)
    
    sequences = []
    targets = []
    
    for _ in range(n_sequences):
        # Generate sequence
        seq = np.random.rand(seq_length, 4)
        
        # Simulate pattern: high discrepancy + high port risk = longer delay
        avg_discrepancy = seq[:, 2].mean()
        avg_port_risk = seq[:, 3].mean()
        
        base_delay = 5
        delay = base_delay + (avg_discrepancy * 10) + (avg_port_risk * 15)
        delay += np.random.normal(0, 2)  # Noise
        delay = max(0, delay)
        
        sequences.append(seq)
        targets.append(delay)
    
    return np.array(sequences), np.array(targets)


def train_model(
    n_sequences: int = 1000,
    seq_length: int = 10,
    epochs: int = 50,
    output_path: str = "models/lstm_payment_delay.pth"
):
    """
    Train LSTM model for payment delay prediction.
    
    Args:
        n_sequences: Number of training sequences
        seq_length: Length of each sequence
        epochs: Training epochs
        output_path: Path to save model
        
    Returns:
        Final training loss
    """
    logger.info("Generating synthetic training data...")
    sequences, targets = generate_synthetic_sequences(n_sequences, seq_length)
    
    # Create dataset
    dataset = PaymentDelayDataset(sequences, targets)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Initialize model
    model = PaymentDelayLSTM(input_size=4, hidden_size=64, num_layers=2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    logger.info("Training LSTM...")
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        for batch_sequences, batch_targets in dataloader:
            optimizer.zero_grad()
            
            predictions = model(batch_sequences).squeeze()
            loss = criterion(predictions, batch_targets)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    # Save model
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)
    logger.info(f"Model saved to {output_path}")
    
    return avg_loss


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    final_loss = train_model(n_sequences=1000, epochs=50)
    print(f"\nTraining complete! Final loss: {final_loss:.4f}")
