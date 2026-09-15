#pragma once

#include <NEMain.h>

#include "math/Angle.h"
#include "render/AssetService.h"

class InputService;
class RenderService;

// A mushroom held up close on the 3D screen (which is the touch screen while
// inspecting): drag to turn it, including looking at the underside, with a
// little inertia. Two icons: put it back (hand) and "this one!" (basket).
class InspectionView
{
public:
    enum class Action
    {
        None,
        Back,
        Choose,
    };

    explicit InspectionView(const AssetService &assets) : assets_(assets) {}

    void Init();
    void Show(ModelId model);
    Action Update(const InputService &input);
    void Draw(const RenderService &render) const;

private:
    const AssetService &assets_;
    NE_Camera *camera_ = nullptr;
    NE_Material *icons_ = nullptr;
    ModelId model_ = ModelId::DetailSteinpilz;

    Angle yaw_;
    s32 pitch_ = 0; // binary angle, clamped
    s32 yawSpeed_ = 0;
    s32 pitchSpeed_ = 0;
    bool dragging_ = false;
    int lastX_ = 0;
    int lastY_ = 0;
    int frame_ = 0;
};
