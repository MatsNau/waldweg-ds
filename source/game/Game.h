#pragma once

#include "core/Services.h"
#include "game/EndingState.h"
#include "game/ExploreState.h"
#include "game/GameProgress.h"
#include "game/GameState.h"
#include "game/IdentifySession.h"
#include "game/IdentifyState.h"

// State machine of the whole game. States are preallocated members; a state
// change requested during Update takes effect at the start of the next frame.
class Game : public StateMachine
{
public:
    explicit Game(Services &services);

    void Init();
    void Update();
    void Draw3D();

    void ChangeState(StateId id) override;
    void StartNewGame() override;

private:
    GameState &StateFor(StateId id);

    Services &services_;
    GameProgress progress_;
    IdentifySession session_;
    ExploreState explore_;
    IdentifyState identify_;
    EndingState ending_;

    GameState *current_ = nullptr;
    GameState *pending_ = nullptr;
};
