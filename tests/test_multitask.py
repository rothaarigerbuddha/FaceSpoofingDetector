"""Smoke tests for AENet multi-task (AENet_C,S) supervision.

These need torch (skipped otherwise). They run on CPU with synthetic tensors, so
they require neither the dataset nor a GPU. They verify the four things the thesis
experiment relies on:
    1. the inference path (fc_live only) is unchanged,
    2. the auxiliary heads actually receive gradients,
    3. every per-head loss decreases when overfitting a fixed batch,
    4. the attribute loss is correctly masked to live images.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from fsd.detectors.aenet import AENet  # noqa: E402
from fsd.dataset.celeba_spoof import LABEL_VECTOR_LEN, LabelEntry  # noqa: E402
from fsd.multitask import AuxWeights, aux_targets, multitask_loss  # noqa: E402


def _entry(live_spoof: int, spoof_type: int, illum: int, attrs):
    vec = [0] * LABEL_VECTOR_LEN
    vec[:40] = list(attrs)
    vec[40] = spoof_type
    vec[41] = illum
    vec[43] = live_spoof
    return LabelEntry(path="x.png", raw=tuple(vec))


def _collate(items):
    from torch.utils.data._utils.collate import default_collate

    return default_collate(items)


def test_forward_shapes_and_inference_unchanged():
    model = AENet(num_classes=2).eval()
    x = torch.randn(4, 3, 224, 224)
    # Inference path: only the live/spoof head, shape (B, 2) -- unchanged.
    out = model(x)
    assert out.shape == (4, 2)
    heads = model.forward_multitask(x)
    assert heads["live"].shape == (4, 2)
    assert heads["attack"].shape == (4, 11)
    assert heads["light"].shape == (4, 5)
    assert heads["attribute"].shape == (4, 40)
    # forward_multitask's live head must match the plain forward exactly.
    assert torch.allclose(out, heads["live"], atol=1e-6)


def test_aux_targets_masking():
    live = aux_targets(_entry(0, 0, 0, [1] * 40))
    spoof = aux_targets(_entry(1, 3, 2, [0] * 40))
    assert live["attr_valid"] == 1.0 and live["live"] == 0
    assert spoof["attr_valid"] == 0.0 and spoof["live"] == 1
    assert spoof["attack"] == 3 and spoof["light"] == 2


def test_auxiliary_heads_receive_gradients():
    model = AENet(num_classes=2).train()
    batch = _collate([
        aux_targets(_entry(0, 0, 0, [1, 0] * 20)),
        aux_targets(_entry(1, 3, 2, [0] * 40)),
    ])
    x = torch.randn(2, 3, 224, 224)
    heads = model.forward_multitask(x)
    loss, log = multitask_loss(heads, batch, AuxWeights())
    loss.backward()
    for head in (model.fc_live, model.fc_attack, model.fc_light, model.fc_live_attribute):
        g = head.weight.grad
        assert g is not None and torch.any(g != 0), "auxiliary head got no gradient"
    assert set(log) == {"live", "attack", "light", "attribute", "total"}


def test_attribute_loss_masked_to_live_only():
    # An all-spoof batch must produce zero attribute loss and no attribute-head grad.
    model = AENet(num_classes=2).train()
    batch = _collate([
        aux_targets(_entry(1, 3, 2, [1] * 40)),
        aux_targets(_entry(1, 9, 4, [1] * 40)),
    ])
    x = torch.randn(2, 3, 224, 224)
    heads = model.forward_multitask(x)
    loss, log = multitask_loss(heads, batch, AuxWeights())
    assert log["attribute"] == 0.0
    loss.backward()
    g = model.fc_live_attribute.weight.grad
    assert g is None or torch.all(g == 0), "spoof-only batch must not train the attribute head"


def test_every_head_loss_decreases_on_overfit():
    torch.manual_seed(0)
    model = AENet(num_classes=2).train()
    # A fixed 6-image batch (3 live / 3 spoof) the model should memorise.
    items = [
        aux_targets(_entry(0, 0, 0, [1, 0] * 20)),
        aux_targets(_entry(0, 0, 0, [0, 1] * 20)),
        aux_targets(_entry(0, 0, 0, [1] * 40)),
        aux_targets(_entry(1, 1, 1, [0] * 40)),
        aux_targets(_entry(1, 5, 3, [0] * 40)),
        aux_targets(_entry(1, 9, 4, [0] * 40)),
    ]
    batch = _collate(items)
    x = torch.randn(6, 3, 224, 224)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    first = last = None
    for step in range(60):
        opt.zero_grad()
        heads = model.forward_multitask(x)
        loss, log = multitask_loss(heads, batch, AuxWeights())
        loss.backward()
        opt.step()
        if step == 0:
            first = log
        last = log
    for head in ("live", "attack", "light", "attribute"):
        assert last[head] < first[head], f"{head} loss did not decrease ({first[head]:.3f} -> {last[head]:.3f})"
