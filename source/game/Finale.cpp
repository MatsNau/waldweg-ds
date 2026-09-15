#include "game/Finale.h"

#include "entities/Mats.h"
#include "entities/Nina.h"
#include "game/GameState.h"
#include "ui/DialogBox.h"
#include "ui/ScreenFader.h"
#include "world/CameraRig.h"

namespace {

// Positions relative to the shrine.
constexpr Vec2 kCowSpawn = { -7_fx, -4_fx };    // among the trees, north-west
constexpr Vec2 kCowAtAltar = { -1.9_fx, 0.3_fx }; // next to the altar stone
constexpr Vec2 kGiantSpot = { -4.2_fx, 0.6_fx };  // steps back while growing

constexpr Fixed kWalkSpeed = 0.035_fx;
constexpr Fixed kRideSpeed = 0.06_fx;
constexpr Fixed kGiantScale = 4_fx;
constexpr Fixed kExitZ = 11.5_fx;
// Far beyond the exit, so Shroomchen never arrives and keeps walking into the dark.
constexpr Fixed kWalkOutZ = 60_fx;

constexpr int kSniffFrames = 100;
constexpr int kGrowFrames = 160;
constexpr int kFadeFrames = 50;

// Riders on the back, measured along the cow (at scale 1).
constexpr Fixed kNinaSeat = 0.15_fx;
constexpr Fixed kMatsSeat = -0.3_fx;

constexpr int kFogNight = 0x7B80;
constexpr int kFogGlowing = 0x7F60; // far away: the camera pulls back a lot
constexpr u32 kGlowColor = RGB15(27, 29, 31);

// Smoothstep 0..1 for gentle growth.
Fixed Ease(Fixed t)
{
    return t * t * (3_fx - t * 2);
}

} // namespace

void Finale::Reset()
{
    phase_ = Phase::Inactive;
    riding_ = false;
    cow_.SetVisible(false);
    cow_.SetDeity(false);
    cow_.SetScale(1_fx);
}

void Finale::Start(Vec2 shrine)
{
    shrine_ = shrine;
    Vec2 spawn = shrine + kCowSpawn;
    cow_.Place(spawn, Angle::FromDirection(shrine + kCowAtAltar - spawn));
    cow_.SetVisible(true);
    Enter(Phase::Arrive);
}

void Finale::Enter(Phase phase)
{
    phase_ = phase;
    timer_ = 0;
}

void Finale::SeatRiders(Nina &nina, Mats &mats)
{
    Fixed height = cow_.SeatHeight();
    nina.Place(cow_.SeatPosition(kNinaSeat), cow_.Facing());
    nina.SetElevation(height);
    mats.Place(cow_.SeatPosition(kMatsSeat), cow_.Facing());
    mats.SetElevation(height);
}

void Finale::Update(Nina &nina, Mats &mats, CameraRig &camera, RenderService &render)
{
    if (!IsActive())
        return;
    timer_++;

    light_.position = cow_.Position();
    light_.radius = 3_fx * cow_.Scale();
    light_.color = kGlowColor;

    // Nina and Mats watch (or ride); they don't walk during the sequence.
    if (riding_)
        SeatRiders(nina, mats);
    nina.Idle();
    mats.Idle();

    switch (phase_)
    {
        case Phase::Inactive:
            break;

        case Phase::Arrive:
            camera.Follow((nina.Position() + shrine_) * 0.5_fx);
            if (cow_.WalkTowards(shrine_ + kCowAtAltar, kWalkSpeed))
                Enter(Phase::Sniff);
            break;

        case Phase::Sniff:
            // Turn to the offering and sniff at it for a moment.
            cow_.TurnTowards(Angle::FromDegrees(90), 600);
            cow_.Stand();
            camera.Follow(shrine_);
            if (timer_ >= kSniffFrames)
            {
                growStart_ = cow_.Position();
                cow_.SetDeity(true);
                camera.SetZoom(1.9_fx);
                Enter(Phase::Grow);
            }
            break;

        case Phase::Grow:
        {
            Fixed t = Ease(Fixed::FromInt(timer_) / kGrowFrames);
            cow_.SetScale(1_fx + (kGiantScale - 1_fx) * t);
            cow_.Move(growStart_ + ((shrine_ + kGiantSpot) - growStart_) * t);
            cow_.Stand();
            render.SetFogOverride(kFogNight + ((kFogGlowing - kFogNight) * t.Raw() >> Fixed::kShift));
            camera.Follow(shrine_ + (kGiantSpot * 0.5_fx));
            if (timer_ >= kGrowFrames)
            {
                dialog_.Say("Shroomchen", "Muh.");
                Enter(Phase::Speak);
            }
            break;
        }

        case Phase::Speak:
            cow_.Stand();
            camera.Follow(shrine_ + (kGiantSpot * 0.5_fx));
            if (!dialog_.HasQueuedMessages())
            {
                fader_.FadeOut(kFadeFrames);
                Enter(Phase::FadeToRide);
            }
            break;

        case Phase::FadeToRide:
            cow_.Stand();
            if (fader_.IsBlack())
            {
                // Facing south, towards the edge of the forest.
                cow_.Place(cow_.Position(), Angle());
                riding_ = true;
                SeatRiders(nina, mats);
                camera.SetZoom(2.3_fx);
                camera.SnapTo(cow_.Position());
                fader_.FadeIn(kFadeFrames);
                Enter(Phase::Ride);
            }
            break;

        case Phase::Ride:
        {
            cow_.WalkTowards({ cow_.Position().x, kWalkOutZ }, kRideSpeed);
            camera.Follow(cow_.Position());
            if (cow_.Position().z >= kExitZ && !fader_.IsBusy())
            {
                fader_.FadeOut(kFadeFrames * 2);
                Enter(Phase::FadeToEnd);
            }
            break;
        }

        case Phase::FadeToEnd:
            cow_.WalkTowards({ cow_.Position().x, kWalkOutZ }, kRideSpeed);
            camera.Follow(cow_.Position());
            if (fader_.IsBlack())
            {
                machine_.ChangeState(StateId::Ending);
                phase_ = Phase::Inactive;
            }
            break;
    }
}
