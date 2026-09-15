#include "ui/InspectionView.h"

#include "core/Fatal.h"
#include "core/InputService.h"
#include "render/RenderService.h"
#include "ui/UiLayout.h"

namespace {

constexpr const char *kIconsPath = "textures/icons3d.grf";

// Screen rectangles of the two icons (bottom corners).
constexpr ui::Rect kBackButton = { 6, 150, 36, 36 };
constexpr ui::Rect kChooseButton = { 214, 150, 36, 36 };

constexpr Fixed kCameraDistance = 2.2_fx;
constexpr Fixed kPivotHeight = 0.6_fx; // models are ~1.2 units tall, origin at the base

constexpr s32 kTurnPerPixel = 220;                       // binary angle units
constexpr s32 kPitchLimit = Angle::kFullTurn * 100 / 360; // allows looking underneath
constexpr s32 kStartYaw = Angle::kFullTurn * 20 / 360;
constexpr s32 kStartPitch = Angle::kFullTurn * 12 / 360;

constexpr u32 kPolygonIdBackground = 60;
constexpr u32 kPolygonIdButtons = 61;
constexpr s16 kDepthBackground = 3900; // far
constexpr s16 kDepthButton = -3300;
constexpr s16 kDepthIcon = -3600;

constexpr u32 kBackgroundTop = RGB15(26, 22, 15);
constexpr u32 kBackgroundBottom = RGB15(17, 19, 11);
constexpr u32 kButtonColor = RGB15(29, 26, 21);

s32 ClampPitch(s32 pitch)
{
    if (pitch > kPitchLimit)
        return kPitchLimit;
    if (pitch < -kPitchLimit)
        return -kPitchLimit;
    return pitch;
}

} // namespace

void InspectionView::Init()
{
    camera_ = NE_CameraCreate();
    icons_ = NE_MaterialCreate();
    if (camera_ == nullptr || NE_MaterialTexLoadGRF(icons_, nullptr, NE_TEXGEN_TEXCOORD, kIconsPath) == 0)
        Fatal("Textur fehlt:\n%s", kIconsPath);

    NE_CameraSetI(camera_, 0, 0, kCameraDistance.Raw(), 0, 0, 0, 0, Fixed::kOne, 0);
}

void InspectionView::Show(ModelId model)
{
    model_ = model;
    yaw_ = Angle::FromBinary(kStartYaw);
    pitch_ = kStartPitch;
    yawSpeed_ = 0;
    pitchSpeed_ = 0;
    dragging_ = false;
}

InspectionView::Action InspectionView::Update(const InputService &input)
{
    frame_++;
    int x = input.TouchX();
    int y = input.TouchY();

    if (input.IsPressed(Button::Touch))
    {
        if (kBackButton.Contains(x, y))
            return Action::Back;
        if (kChooseButton.Contains(x, y))
            return Action::Choose;

        dragging_ = true;
        lastX_ = x;
        lastY_ = y;
        yawSpeed_ = 0;
        pitchSpeed_ = 0;
    }

    if (dragging_ && input.IsTouching())
    {
        yawSpeed_ = (x - lastX_) * kTurnPerPixel;
        pitchSpeed_ = (y - lastY_) * kTurnPerPixel;
        lastX_ = x;
        lastY_ = y;
    }
    else
    {
        dragging_ = false;
        // Let the mushroom spin out gently.
        yawSpeed_ -= yawSpeed_ / 8 + (yawSpeed_ > 0) - (yawSpeed_ < 0);
        pitchSpeed_ -= pitchSpeed_ / 4 + (pitchSpeed_ > 0) - (pitchSpeed_ < 0);
    }

    yaw_ = yaw_ + Angle::FromBinary(yawSpeed_);
    pitch_ = ClampPitch(pitch_ + pitchSpeed_);
    return Action::None;
}

void InspectionView::Draw(const RenderService &render) const
{
    NE_CameraUse(camera_);
    render.ClearObjectLight();

    NE_ViewPush();
    NE_ViewRotate(NitroRotation(pitch_), yaw_.ToNitro(), 0);
    NE_ViewMoveI(0, -kPivotHeight.Raw(), 0);

    NE_Model *model = assets_.Model(model_);
    NE_ModelSetCoordI(model, 0, 0, 0);
    NE_ModelSetRot(model, 0, 0, 0);
    Lighting lighting = AssetService::IsGlowing(model_) ? Lighting::Glow : Lighting::LitTwoSided;
    render.BeginPolygons(PolyGroup::Mushrooms, 0, lighting);
    NE_ModelDraw(model);
    NE_ViewPop();

    // 2D: soft background behind the mushroom and the two icons.
    NE_2DViewInit();
    NE_PolyFormat(31, kPolygonIdBackground, static_cast<NE_LightEnum>(0), NE_CULL_NONE,
                  static_cast<NE_OtherFormatEnum>(0));
    NE_2DDrawQuadGradient(0, 0, 256, 192, kDepthBackground, kBackgroundTop, kBackgroundTop,
                          kBackgroundBottom, kBackgroundBottom);

    NE_PolyFormat(31, kPolygonIdButtons, static_cast<NE_LightEnum>(0), NE_CULL_NONE,
                  static_cast<NE_OtherFormatEnum>(0));
    // The basket bobs slightly, inviting a tap.
    int bob = ((frame_ / 24) % 2 == 0) ? 0 : -1;
    const ui::Rect buttons[] = { kBackButton, kChooseButton };
    for (int i = 0; i < 2; i++)
    {
        const ui::Rect &r = buttons[i];
        int offset = i == 1 ? bob : 0;
        NE_2DDrawQuad(r.x, r.y + offset, r.x + r.w, r.y + r.h + offset, kDepthButton, kButtonColor);
        // Icon atlas: basket at u = 0, hand at u = 32.
        RenderService::Draw2DImage(icons_, r.x + 2, r.y + 2 + offset, 32, 32, i == 1 ? 0 : 32, 0, 32, 32,
                                   kDepthIcon, RGB15(31, 31, 31));
    }
}
