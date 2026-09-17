#include "game/ExploreState.h"

#include <time.h>

#include "audio/AudioService.h"
#include "core/InputService.h"
#include "game/GameProgress.h"
#include "ui/SubScreenService.h"
#include "ui/TextService.h"
#include "ui/TopTextService.h"
#include "ui/UiLayout.h"
#include "world/TimeOfDayService.h"

namespace {

constexpr u32 kForestSeed = 0x57A1D;
constexpr u32 kMushroomSeed = 0xB1E7E;
constexpr Vec2 kMatsSpawnOffset = { -0.8_fx, 0.9_fx };
constexpr int kFogStep = 0x10;
constexpr int kNewGameFadeFrames = 90;

constexpr Fixed kShrineNear = 3.2_fx;   // first visit comment
constexpr Fixed kShrineReach = 2.6_fx;  // tapping the shrine
constexpr Fixed kShrineTapRadius = 1.4_fx;
constexpr Fixed kAltarTop = 0.64_fx;    // top of the altar stone (models_world.py)

} // namespace

ExploreState::ExploreState(Services &services, StateMachine &machine, GameProgress &progress,
                           IdentifySession &session)
    : services_(services),
      machine_(machine),
      progress_(progress),
      session_(session),
      forest_(services.assets),
      mushrooms_(services.assets),
      nina_(services.assets),
      mats_(services.assets),
      lantern_(services.assets),
      shadows_(services.assets),
      leaves_(services.assets, 0x1EAF),
      map_(services.subScreen),
      backpack_(services.subScreen),
      hud_(services),
      story_(services, progress, dialog_, nina_, mats_),
      finale_(services.assets, dialog_, fader_, machine)
{
}

void ExploreState::Init()
{
    forest_.Generate(kForestSeed);
    camera_.Init();
    backpack_.Init();
    map_.Build(forest_);
}

void ExploreState::StartNewGame()
{
    finale_.Reset();
    services_.render.SetFogOverride(-1);
    camera_.SetZoom(1_fx);
    nina_.SetElevation(0_fx);
    mats_.SetElevation(0_fx);
    u32 godSeed = static_cast<u32>(time(nullptr)) * 2654435761u ^ REG_VCOUNT;
    mushrooms_.Generate(forest_, kMushroomSeed, godSeed);
    leaves_.Clear();

    // Facing away from the camera, into the forest.
    Angle north = Angle::FromDegrees(180);
    Vec2 spawn = forest_.SpawnPoint();

    nina_.Place(spawn, north);
    mats_.Place(spawn + kMatsSpawnOffset, north);
    camera_.SnapTo(spawn);

    story_.Start();
}

void ExploreState::Enter()
{
    hudShown_ = false;
    if (newGameOnEnter_)
    {
        newGameOnEnter_ = false;
        restarting_ = false;
        finaleStartPending_ = false;
        StartNewGame();
        backpack_.ShowFixedSprites();
        fader_.SetBlack();
        fader_.FadeIn(kNewGameFadeFrames);
    }
    ApplyIdentifyResult();
}

void ExploreState::ApplyIdentifyResult()
{
    if (session_.outcome == IdentifySession::Outcome::Chosen)
    {
        mushrooms_.Pick(session_.mushroomIndex);
        story_.OnIdentified(session_.actual, session_.chosen);
    }
    session_.outcome = IdentifySession::Outcome::None;
}

void ExploreState::UpdateRestart()
{
    fader_.Update();

    if (!restarting_ && story_.IsRestartRequested() && !dialog_.HasQueuedMessages())
    {
        restarting_ = true;
        fader_.FadeOut(60);
    }
    if (restarting_ && fader_.IsBlack())
    {
        StartNewGame();
        fader_.FadeIn(60);
        restarting_ = false;
    }
}

void ExploreState::Update()
{
    const InputService &input = services_.input;
    HandleDebugInput();

    UpdateRestart();

    if (story_.ConsumeFinaleRequest())
        finaleStartPending_ = true;
    if (finaleStartPending_ && !dialog_.HasQueuedMessages())
    {
        finaleStartPending_ = false;
        finale_.Start(forest_.ShrinePosition());
    }

    if (finale_.IsActive())
    {
        // Cutscene: no walking, tapping or handing over items.
        bool skip = input.IsPressed(Button::Touch) && ui::kMapArea.Contains(input.TouchX(), input.TouchY());
        dialog_.Update(skip);
        finale_.Update(nina_, mats_, camera_, services_.render);
    }
    else
    {
        // Bottom screen first, so a tap is used by exactly one element.
        ItemId given = backpack_.Update(input, progress_);
        if (given != ItemId::Count)
            story_.OnItemGiven(given);

        // A tap on the map that doesn't hit a mushroom skips the current message.
        bool tapUsed = !backpack_.IsDragging() && !restarting_ && HandleMapTouch();
        bool skip = !tapUsed && input.IsPressed(Button::Touch) &&
                    ui::kMapArea.Contains(input.TouchX(), input.TouchY());
        dialog_.Update(skip);

        nina_.Update(input, forest_);
        mats_.Update(nina_, forest_);
        camera_.Follow(nina_.Position());
    }

    // Mats walks a step behind, so his steps are quieter.
    if (nina_.StepTaken())
        services_.audio.PlayStep(false);
    if (mats_.StepTaken())
        services_.audio.PlayStep(true);

    mushrooms_.SetGodMushroomVisible(progress_.IsGiven(ItemId::Lantern));
    if ((nina_.Position() - forest_.ShrinePosition()).LengthSq() < kShrineNear * kShrineNear)
        story_.OnNearShrine();

    // Once Shroomchen glows, its light replaces the lantern.
    lantern_.SetEnabled(progress_.IsGiven(ItemId::Lantern) && finale_.Light() == nullptr);
    lantern_.Update(mats_.Position());

    // Now and then a leaf tumbles through the picture (fewer in the dark).
    Vec2 focus = camera_.Focus();
    LeafParticles::Area area = { focus, 6_fx, -8_fx, 2_fx, 3.5_fx };
    leaves_.Update(area, progress_.IsGiven(ItemId::Lantern) ? 8 : 25);

    story_.Update();
    backpack_.SetMatsMood(story_.Mood());
    map_.Update(nina_.Position(), mats_.Position(), mushrooms_);
    UpdateText();
}

bool ExploreState::HandleMapTouch()
{
    const InputService &input = services_.input;
    if (!input.IsPressed(Button::Touch))
        return false;

    Vec2 world;
    if (!map_.ScreenToWorld(input.TouchX(), input.TouchY(), world))
        return false;

    int index = mushrooms_.FindNear(world, ForestMap::kTapRadius);
    if (index < 0)
    {
        // The shrine: place the offering.
        Vec2 shrine = forest_.ShrinePosition();
        bool tappedShrine = (world - shrine).LengthSq() < kShrineTapRadius * kShrineTapRadius;
        bool nearShrine = (nina_.Position() - shrine).LengthSq() < kShrineReach * kShrineReach;
        return tappedShrine && nearShrine && story_.OnShrineTapped();
    }

    // Out of reach: nothing happens, Nina has to walk closer (the map icon
    // blinks once she is near enough).
    if (!mushrooms_.IsInReach(index, nina_.Position()))
        return true;
    if (mushrooms_.At(index).species == SpeciesId::WaldgottPilz)
    {
        // No book needed: this one is simply taken along.
        mushrooms_.Pick(index);
        story_.OnOfferingTaken();
        return true;
    }
    if (!story_.RequestPick())
        return true;

    // Look at it closely and find it in the book.
    session_.mushroomIndex = index;
    session_.actual = mushrooms_.At(index).species;
    session_.outcome = IdentifySession::Outcome::None;
    machine_.ChangeState(StateId::Identify);
    return true;
}

void ExploreState::UpdateText()
{
    // Dialogs on the top screen.
    dialog_.Draw(services_.topText);

    // Debug HUD in the parchment panel of the bottom screen.
    TextService &text = services_.text;
    if (hud_.IsVisible() != hudShown_)
    {
        hudShown_ = hud_.IsVisible();
        services_.subScreen.ShowDialogPanel(hudShown_);
        text.Clear();
        text.Present();
        hud_.RequestRefresh();
    }
    if (hudShown_ && hud_.Draw(nina_, mats_, forest_, mushrooms_))
        text.Present();
}

void ExploreState::Draw3D()
{
    const RenderService &render = services_.render;

    camera_.Use();
    lantern_.Apply(services_.render);
    if (finale_.Light() != nullptr)
        services_.render.SetPointLight(finale_.Light());
    forest_.Draw(render, camera_.Focus());
    mushrooms_.Draw(render, camera_.Focus());
    DrawOffering(render);
    finale_.Draw(render);
    mats_.Draw(render);
    nina_.Draw(render);
    leaves_.Draw(render);

    // Translucent polygons last: shadows, then the lantern's light.
    forest_.DrawShadows(render, shadows_, camera_.Focus());
    if (nina_.Elevation() == 0_fx)
    {
        shadows_.Draw(render, nina_.Position(), 0.28_fx, 1.1_fx);
        shadows_.Draw(render, mats_.Position(), 0.28_fx, 1.15_fx);
    }
    if (finale_.Cow().IsVisible())
    {
        Fixed scale = finale_.Cow().Scale();
        shadows_.Draw(render, finale_.Cow().Position(), 0.55_fx * scale, 1.1_fx * scale);
    }
    lantern_.DrawPool(render);
    // 2D overlay at the very end (changes the projection).
    services_.topText.Draw();
}

void ExploreState::DrawOffering(const RenderService &render) const
{
    if (!progress_.IsOfferingPlaced())
        return;

    Vec2 shrine = forest_.ShrinePosition();
    NE_Model *model = services_.assets.Model(ModelId::WaldgottPilz);
    NE_ModelSetCoordI(model, shrine.x.Raw(), kAltarTop.Raw(), shrine.z.Raw());
    NE_ModelSetRot(model, 0, 0, 0);
    render.BeginPolygons(PolyGroup::Effects, 1, Lighting::Glow);
    NE_ModelDraw(model);
}

void ExploreState::HandleDebugInput()
{
#ifdef WALDWEG_DEBUG
    const InputService &input = services_.input;
    RenderService &render = services_.render;

    if (input.IsPressed(Button::Select) && input.IsHeld(Button::L))
        machine_.ChangeState(StateId::Ending);
    else if (input.IsPressed(Button::Select) && input.IsHeld(Button::R))
        story_.DebugSkipToLantern();
    else if (input.IsPressed(Button::Select))
        services_.timeOfDay.Advance();
    if (input.IsPressed(Button::Start))
        hud_.Toggle();
    if (input.IsHeld(Button::L))
        render.SetFogDepth(render.FogDepth() - kFogStep);
    if (input.IsHeld(Button::R))
        render.SetFogDepth(render.FogDepth() + kFogStep);
#endif
}
