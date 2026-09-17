#pragma once

#include "core/Services.h"
#include "entities/Mats.h"
#include "entities/Nina.h"
#include "game/Finale.h"
#include "game/GameState.h"
#include "game/IdentifySession.h"
#include "game/StoryDirector.h"
#include "ui/Backpack.h"
#include "ui/DebugHud.h"
#include "ui/DialogBox.h"
#include "ui/ForestMap.h"
#include "ui/ScreenFader.h"
#include "world/CameraRig.h"
#include "world/Forest.h"
#include "world/LanternLight.h"
#include "world/LeafParticles.h"
#include "world/ShadowCaster.h"
#include "world/MushroomField.h"

class GameProgress;

// Walking through the forest with Nina, Mats following; mushrooms are picked
// by tapping them on the map, items are handed over from the backpack.
class ExploreState : public GameState
{
public:
    ExploreState(Services &services, StateMachine &machine, GameProgress &progress,
                 IdentifySession &session);

    // One-time setup after the assets are loaded.
    void Init();
    // Resets mushrooms, characters, items and story (new game or restart).
    void StartNewGame();
    // The next Enter() starts a new game, fading in from black.
    void StartNewGameOnEnter() { newGameOnEnter_ = true; }

    void Enter() override;
    void Update() override;
    void Draw3D() override;

private:
    // Returns true if the touch was used (a mushroom was tapped).
    bool HandleMapTouch();
    // Returns true if the player wants the current message to end early.
    bool SkipPressed(bool tapUsed) const;
    void ApplyIdentifyResult();
    void DrawOffering(const RenderService &render) const;
    void UpdateRestart();
    void UpdateText();
    void HandleDebugInput();

    Services &services_;
    StateMachine &machine_;
    GameProgress &progress_;
    IdentifySession &session_;

    Forest forest_;
    MushroomField mushrooms_;
    CameraRig camera_;
    Nina nina_;
    Mats mats_;
    LanternLight lantern_;
    ShadowCaster shadows_;
    LeafParticles leaves_;

    ForestMap map_;
    Backpack backpack_;
    DialogBox dialog_;
    DebugHud hud_;
    StoryDirector story_;
    ScreenFader fader_;
    Finale finale_;
    bool hudShown_ = false;
    bool restarting_ = false;
    bool finaleStartPending_ = false;
    bool newGameOnEnter_ = false;
};
