#include "entities/CharacterRig.h"

namespace {

// Joint positions in character space; keep in sync with
// assets/blender/models_characters.py (HIP_Z, LEG_X, SHOULDER_X, ...).
// The character faces +Z, so its left side is +X.
constexpr Fixed kHipY = 0.34_fx;
constexpr Fixed kLegX = 0.075_fx;
constexpr Fixed kShoulderX = 0.15_fx;
constexpr Fixed kShoulderY = kHipY + 0.30_fx;
constexpr Fixed kNeckY = kHipY + 0.36_fx;
// Hand position relative to the shoulder (end of the sleeve).
constexpr Fixed kHandY = -0.29_fx;

// Sitting: hips just above the ground, legs forwards, hands resting a bit ahead.
constexpr Fixed kSitDrop = kHipY - 0.1_fx;
constexpr s32 kSitLegAngle = -Angle::kFullTurn * 80 / 360;
constexpr s32 kSitArmAngle = -Angle::kFullTurn * 25 / 360;

// One full step cycle (left + right foot) per this walking distance.
constexpr Fixed kStrideLength = 1.1_fx;
constexpr s32 kLegSwing = Angle::kFullTurn * 32 / 360;
constexpr s32 kArmSwing = Angle::kFullTurn * 28 / 360;
constexpr Fixed kWalkBob = 0.035_fx;
constexpr Fixed kIdleBob = 0.008_fx;
constexpr s32 kIdleArmSway = Angle::kFullTurn * 3 / 360;
constexpr s32 kIdleSpeed = 380; // binary angle units per frame

constexpr Fixed kBlendIn = 0.15_fx;
constexpr Fixed kBlendOut = 0.1_fx;
constexpr Fixed kMovingThreshold = 0.004_fx;

// Polygon IDs inside the character's group (outlines between parts).
enum Part : u32
{
    kPartBody,
    kPartHead,
    kPartLegLeft,
    kPartLegRight,
    kPartArmLeft,
    kPartArmRight,
    kPartItemLeft,  // also the head item
    kPartItemRight, // also the neck item
};

} // namespace

CharacterRig::CharacterRig(const AssetService &assets, const CharacterLook &look)
    : assets_(assets), look_(look)
{
}

void CharacterRig::Update(Fixed distanceMoved)
{
    bool moving = distanceMoved > kMovingThreshold;
    walkBlend_ = fx::Approach(walkBlend_, moving ? 1_fx : 0_fx, moving ? kBlendIn : kBlendOut);

    // Advance the step phase proportional to the distance, so feet don't slide.
    s32 phaseStep = (distanceMoved / kStrideLength).Raw() * Angle::kFullTurn / Fixed::kOne;
    stepPhase_ = stepPhase_ + Angle::FromBinary(phaseStep);
    idlePhase_ = idlePhase_ + Angle::FromBinary(kIdleSpeed);
}

void CharacterRig::SetHandItem(Hand hand, ModelId model)
{
    if (hand == Hand::Left)
        leftHandItem_ = model;
    else
        rightHandItem_ = model;
}

void CharacterRig::Draw(const RenderService &render, Vec2 position, Angle facing, Fixed elevation) const
{
    Fixed swing = stepPhase_.Sin() * walkBlend_;
    Fixed idle = 1_fx - walkBlend_;

    // Bob twice per step cycle (once per foot).
    Fixed bob = fx::Abs(swing) * kWalkBob + idlePhase_.Sin() * kIdleBob * idle;
    s32 legSwing = (swing * kLegSwing).ToInt();
    s32 armSwing = (swing * kArmSwing).ToInt() + (idlePhase_.Cos() * kIdleArmSway * idle).ToInt();

    if (sitting_)
    {
        legSwing = kSitLegAngle;
        armSwing = kSitArmAngle + (idlePhase_.Cos() * kIdleArmSway).ToInt();
        elevation -= kSitDrop;
    }

    NE_ViewPush();
    NE_ViewMoveI(position.x.Raw(), elevation.Raw(), position.z.Raw());
    NE_ViewRotate(0, facing.ToNitro(), 0);
    if (look_.scale != 1_fx)
        NE_ViewScaleI(look_.scale.Raw(), look_.scale.Raw(), look_.scale.Raw());

    DrawPart(render, kPartLegLeft, look_.leg, kLegX, kHipY, legSwing);
    DrawPart(render, kPartLegRight, look_.leg, -kLegX, kHipY, sitting_ ? legSwing : -legSwing);
    DrawPart(render, kPartBody, look_.body, 0_fx, kHipY + bob, 0);
    // Arms swing opposite to the leg on the same side.
    DrawArm(render, kPartArmLeft, kShoulderX, kShoulderY + bob, sitting_ ? armSwing : -armSwing, leftHandItem_);
    DrawArm(render, kPartArmRight, -kShoulderX, kShoulderY + bob, armSwing, rightHandItem_);
    DrawPart(render, kPartHead, look_.head, 0_fx, kNeckY + bob, 0);
    if (neckItem_ != kNothing)
        DrawPart(render, kPartItemRight, neckItem_, 0_fx, kNeckY + bob, 0);
    if (headItem_ != kNothing)
        DrawPart(render, kPartItemLeft, headItem_, 0_fx, kNeckY + bob, 0);

    NE_ViewPop();
}

void CharacterRig::DrawPart(const RenderService &render, u32 part, ModelId modelId,
                            Fixed x, Fixed y, s32 swing, Lighting lighting) const
{
    NE_Model *model = assets_.Model(modelId);
    NE_ModelSetCoordI(model, x.Raw(), y.Raw(), 0);
    NE_ModelSetRot(model, NitroRotation(swing), 0, 0);
    render.BeginPolygons(look_.polyGroup, part, lighting);
    NE_ModelDraw(model);
}

void CharacterRig::DrawArm(const RenderService &render, u32 part, Fixed x, Fixed y, s32 swing,
                           ModelId heldItem) const
{
    // Draw in shoulder space, so a held item follows the swinging arm.
    NE_ViewPush();
    NE_ViewMoveI(x.Raw(), y.Raw(), 0);
    NE_ViewRotate(NitroRotation(swing), 0, 0);

    DrawPart(render, part, look_.arm, 0_fx, 0_fx, 0);
    if (heldItem != kNothing)
    {
        // Counter-rotate so the item hangs roughly downwards.
        u32 itemPart = part == kPartArmLeft ? kPartItemLeft : kPartItemRight;
        DrawPart(render, itemPart, heldItem, 0_fx, kHandY, -swing);

        ModelId glowPart = AssetService::GlowPartOf(heldItem);
        if (glowPart != ModelId::Count)
            DrawPart(render, itemPart, glowPart, 0_fx, kHandY, -swing, Lighting::Glow);
    }

    NE_ViewPop();
}
