/*
 * Copyright (c) 2018 Google Inc. All Rights Reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * Modifications Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <string>

#include "lazy_tensor_core/csrc/device.h"
#include "lazy_tensor_core/csrc/ir.h"
#include "lazy_tensors/span.h"

namespace torch_lazy_tensors {
namespace ir {

class DumpUtil {
 public:
  static std::string ToDot(lazy_tensors::Span<const Node* const> nodes);

  static std::string PostOrderToDot(lazy_tensors::Span<const Node* const> post_order,
                                    lazy_tensors::Span<const Node* const> roots);

  static std::string ToText(lazy_tensors::Span<const Node* const> nodes,
                            bool use_id_order = false);

  static std::string PostOrderToText(lazy_tensors::Span<const Node* const> post_order,
                                     lazy_tensors::Span<const Node* const> roots);

  static std::string ToBackend(lazy_tensors::Span<const Value> values, const Device& device);
};

}  // namespace ir
}  // namespace torch_lazy_tensors
