#pragma once

#include "entities/Shroomchen.h"
#include "render/RenderService.h"

class CameraRig;
class DialogBox;
class Forest;
class Mats;
class Nina;
class ScreenFader;
class StateMachine;

// The ending sequence after the bell rings: a cow walks up to the shrine,
// sniffs at the glowing offering, grows into the giant forest god Shroomchen
// ("Muh."), and carries Nina and Mats out of the forest.
class Finale
{
public:
    Finale(const AssetService &assets, DialogBox &dialog, ScreenFader &fader, StateMachine &machine)
        : cow_(assets), dialog_(dialog), fader_(fader), machine_(machine)
    {
    }

    void Start(Vec2 shrine);
    void Reset();
    bool IsActive() const { return phase_ != Phase::Inactive; }

    // Drives the sequence; takes over the camera and the characters.
    void Update(Nina &nina, Mats &mats, CameraRig &camera, RenderService &render);

    void Draw(const RenderService &render) const { cow_.Draw(render); }
    const Shroomchen &Cow() const { return cow_; }
    // Shroomchen's glow replaces the lantern light once it is a god.
    const PointLight *Light() const { return cow_.Scale() > 1_fx ? &light_ : nullptr; }

private:
    enum class Phase
    {
        Inactive,
        Arrive,
        Sniff,
        Grow,
        Speak,
        FadeToRide,
        Ride,
        FadeToEnd,
    };

    void Enter(Phase phase);
    void SeatRiders(Nina &nina, Mats &mats);

    Shroomchen cow_;
    DialogBox &dialog_;
    ScreenFader &fader_;
    StateMachine &machine_;

    Phase phase_ = Phase::Inactive;
    int timer_ = 0;
    Vec2 shrine_;
    Vec2 growStart_;
    PointLight light_ = {};
    bool riding_ = false;
};
