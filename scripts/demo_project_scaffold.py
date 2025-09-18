from __future__ import annotations

from pathlib import Path

TEMPLATE = """
# tiny training script (PyTorch optional)
try:
    import torch
    x = torch.randn(32, 10)
    y = torch.randn(32, 1)
    model = torch.nn.Linear(10, 1)
    loss_fn = torch.nn.MSELoss()
    opt = torch.optim.SGD(model.parameters(), lr=0.01)
    for _ in range(2):
        opt.zero_grad(); loss = loss_fn(model(x), y); loss.backward(); opt.step()
    print("loss:", float(loss))
except Exception as e:
    print("PyTorch not installed, skipping demo:", e)
"""


def main() -> None:
    p = Path("demo")
    p.mkdir(exist_ok=True)
    (p / "train.py").write_text(TEMPLATE)
    print("Demo scaffold created in ./demo")


if __name__ == "__main__":
    main()
