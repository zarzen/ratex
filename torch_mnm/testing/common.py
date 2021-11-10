"""Common utilities for testing."""
# pylint: disable=too-many-locals, unused-import, too-many-arguments
import copy
import functools
import logging
import random
import sys

import numpy as np

import lazy_tensor_core
import lazy_tensor_core.core.lazy_model as lm
import torch
from torch import nn
import torch.nn.functional as F
from torch import optim

import torch_mnm


class TorchLeNet(nn.Module):
    """LeNet in PyTorch."""

    # pylint: disable=missing-docstring
    def __init__(self, input_shape=28, num_classes=10):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, padding=2, bias=False)
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, bias=False)
        self.linear1 = nn.Linear(((input_shape // 2 - 4) // 2) ** 2 * 16, 120)
        self.linear2 = nn.Linear(120, 84)
        self.linear3 = nn.Linear(84, num_classes)

    def forward(self, x):
        out = self.conv1(x)
        out = torch.relu(out)
        out = F.avg_pool2d(out, (2, 2), (2, 2))
        out = self.conv2(out)
        out = torch.relu(out)  # pylint: disable=no-member
        out = F.avg_pool2d(out, (2, 2), (2, 2))
        out = torch.flatten(out, 1)  # pylint: disable=no-member
        out = self.linear1(out)
        out = self.linear2(out)
        out = self.linear3(out)
        return out


def default_logger():
    """A logger used to output seed information to logs."""
    logger = logging.getLogger(__name__)
    # getLogger() lookups will return the same logger, but only add the handler once.
    if len(logger.handlers) == 0:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        if logger.getEffectiveLevel() == logging.NOTSET:
            logger.setLevel(logging.INFO)
    return logger


def with_seed(seed=None):
    """
    A decorator for test functions that manages rng seeds.

    Parameters
    ----------

    seed : the seed to pass to np.random and random


    This tests decorator sets the np and python random seeds identically
    prior to each test, then outputs those seeds if the test fails or
    if the test requires a fixed seed (as a reminder to make the test
    more robust against random data).

    @with_seed()
    def test_ok_with_random_data():
        ...

    @with_seed(1234)
    def test_not_ok_with_random_data():
        ...

    Use of the @with_seed() decorator for all tests creates
    tests isolation and reproducability of failures.  When a
    test fails, the decorator outputs the seed used.
    """

    def test_helper(orig_test):
        @functools.wraps(orig_test)
        def test_new(*args, **kwargs):
            if seed is not None:
                this_test_seed = seed
                log_level = logging.INFO
            else:
                this_test_seed = np.random.randint(0, np.iinfo(np.int32).max)
                log_level = logging.DEBUG
            post_test_state = np.random.get_state()
            np.random.seed(this_test_seed)
            random.seed(this_test_seed)
            logger = default_logger()
            # 'pytest --logging-level=DEBUG' shows this msg even with an ensuing core dump.
            pre_test_msg = (
                f"Setting test np/python random seeds, use seed={this_test_seed}" " to reproduce."
            )
            on_err_test_msg = (
                f"Error seen with seeded test, use seed={this_test_seed}" " to reproduce."
            )
            logger.log(log_level, pre_test_msg)
            try:
                ret = orig_test(*args, **kwargs)
            except:
                # With exceptions, repeat test_msg at WARNING level to be sure it's seen.
                if log_level < logging.WARNING:
                    logger.warning(on_err_test_msg)
                raise
            finally:
                # Provide test-isolation for any test having this decorator
                np.random.set_state(post_test_state)
            return ret

        return test_new

    return test_helper


def fake_image_dataset(batch, channel, image_size, num_classes):
    """Fake an image dataset."""
    from torchvision import datasets, transforms  # pylint: disable=import-outside-toplevel

    return datasets.FakeData(
        size=batch,
        image_size=(channel, image_size, image_size),
        num_classes=num_classes,
        transform=transforms.Compose([transforms.CenterCrop(image_size), transforms.ToTensor()]),
    )


def train(device, model, dataset, optimizer=optim.SGD, batch_size=1, num_epochs=10, amp=False):
    """Run training."""
    results = []
    model = copy.deepcopy(model)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=False, num_workers=1
    )
    dataset_size = len(dataset)
    model = model.to(device, dtype=torch.float32)
    model.train()

    # adapting loss cacluation from
    # https://www.programmersought.com/article/86167037001/
    # this doesn't match nn.NLLLoss() exactly, but close...
    criterion = lambda pred, true: -torch.sum(pred * true) / true.size(0)
    optimizer = optimizer(model.parameters(), lr=0.001)
    if device == "xla":
        model = torch_mnm.jit.script(model)

    for epoch in range(num_epochs):
        running_loss = []
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            with torch_mnm.amp.autocast(amp):
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                lm.mark_step()
            running_loss.append((loss, inputs.size(0)))

        epoch_loss = sum([l.item() * w for l, w in running_loss]) / dataset_size
        print(f"Epoch {epoch:2d}, Loss {epoch_loss:.4f}", flush=True)
        results.append(epoch_loss)
    return results


def verify(xla_results, cpu_results, tol=1e-5):
    """Verify the series of losses."""
    print("xla_losses = ", xla_results)
    print("cpu_losses = ", cpu_results)
    for xla, cpu in zip(xla_results, cpu_results):
        torch.testing.assert_close(xla, cpu, atol=tol, rtol=tol)
