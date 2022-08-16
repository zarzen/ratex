/*
 * Copyright (c) 2018 Google Inc. All Rights Reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * Modifications Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

#include "lazy_tensor_core/csrc/ops/constant.h"

#include <algorithm>
#include <sstream>

namespace torch_lazy_tensors {
namespace ir {
namespace ops {

Constant::Constant(lazy_tensors::Literal value)
    : Node(OpKind(at::prim::Constant), value.shape(), /*num_outputs=*/1, value.Hash()),
      value_(std::move(value)) {
}

std::string Constant::ToString() const {
  // The Literal to string conversion produces \n separated content, which we do
  // not want. It can also produce giant strings, but that's a different issue.
  LTC_LOG(INFO) << Node::ToString();
  // std::string value_as_string = value_.ToStringWithoutShape();
  // std::replace(value_as_string.begin(), value_as_string.end(), '\n', ';');
  std::stringstream ss;
  // ss << Node::ToString() << ", value=" << value_as_string;
  ss << Node::ToString();
  return ss.str();
}

NodePtr Constant::Clone(OpList operands) const {
  return MakeNode<Constant>(value_.Clone());
}

}  // namespace ops
}  // namespace ir
}  // namespace torch_lazy_tensors
