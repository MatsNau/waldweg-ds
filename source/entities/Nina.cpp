#include "entities/Nina.h"

#include "core/InputService.h"

namespace {

constexpr CharacterLook kNinaLook = {
    ModelId::NinaHead, ModelId::NinaBody, ModelId::NinaArm, ModelId::NinaLeg,
    PolyGroup::Nina, 1_fx,
};

} // namespace

Nina::Nina(const AssetService &assets) : Character(assets, kNinaLook)
{
}

void Nina::SetWearingHat(bool wearing)
{
    Rig().SetHeadItem(wearing ? ModelId::WoolHat : CharacterRig::kNothing);
}

void Nina::Update(const InputService &input, const Forest &forest)
{
    Walk(input.MoveDirection() * kWalkSpeed, forest);
}
