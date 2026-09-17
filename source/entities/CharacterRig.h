#pragma once

#include "math/Angle.h"
#include "render/AssetService.h"
#include "render/RenderService.h"

// Which models and settings make up a character.
struct CharacterLook
{
    ModelId head;
    ModelId body;
    ModelId arm;
    ModelId leg;
    PolyGroup polyGroup;
    Fixed scale;
};

enum class Hand
{
    Left,
    Right,
};

// Draws a character from rigid parts and animates them procedurally:
// legs and arms swing while walking, the body bobs, idle breathing when standing.
// Items can be attached to the hands (swing with the arm) or the neck.
class CharacterRig
{
public:
    static constexpr ModelId kNothing = ModelId::Count;

    CharacterRig(const AssetService &assets, const CharacterLook &look);

    // distanceMoved: how far the character moved this frame (drives the steps).
    void Update(Fixed distanceMoved);

    // True on the frame a foot lands, for the footstep sound. Two per cycle.
    bool StepTaken() const { return stepTaken_; }

    void SetHandItem(Hand hand, ModelId model);
    void SetNeckItem(ModelId model) { neckItem_ = model; }
    void SetHeadItem(ModelId model) { headItem_ = model; }
    // Sitting on the ground, legs stretched out forwards.
    void SetSitting(bool sitting) { sitting_ = sitting; }

    void Draw(const RenderService &render, Vec2 position, Angle facing, Fixed elevation = 0_fx) const;

private:
    void DrawPart(const RenderService &render, u32 part, ModelId model,
                  Fixed x, Fixed y, s32 swing, Lighting lighting = Lighting::Lit) const;
    void DrawArm(const RenderService &render, u32 part, Fixed x, Fixed y, s32 swing,
                 ModelId heldItem) const;

    // Models are looked up when drawing, because the rig is constructed
    // before AssetService has loaded them.
    const AssetService &assets_;
    CharacterLook look_;
    ModelId leftHandItem_ = kNothing;
    ModelId rightHandItem_ = kNothing;
    ModelId neckItem_ = kNothing;
    ModelId headItem_ = kNothing;
    bool sitting_ = false;

    Angle stepPhase_;
    Angle idlePhase_;
    Fixed walkBlend_; // 0 = standing, 1 = walking
    bool stepTaken_ = false;
    int stepHalf_ = 0;
    int footfalls_ = 0;
};
