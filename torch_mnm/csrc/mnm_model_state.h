#pragma once

#include <unordered_set>

#include "lazy_tensor_core/csrc/compiler/backend_impl_interface.h"
#include "lazy_tensor_core/csrc/tensor.h"

namespace torch_lazy_tensors {

class MNMModelState {
 public:
  static MNMModelState* Get();

  bool IsModelState(const LazyTensor& tensor);
  void AddModelState(const LazyTensor& tensor);

  bool IsAMPEnabled();
  void SetAMPEnabled(bool enabled);

 private:
  bool enable_amp_ = false;
  std::unordered_set<lazy_tensors::int64> model_state_;
};

MNMModelState* GetMNMModelState();

}  // namespace torch_lazy_tensors
