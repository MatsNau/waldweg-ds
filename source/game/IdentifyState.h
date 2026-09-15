#pragma once

#include "core/Services.h"
#include "game/GameState.h"
#include "game/IdentifySession.h"
#include "ui/BookView.h"
#include "ui/InspectionView.h"

// Identifying a tapped mushroom. The screens are swapped: the book is shown on
// the upper screen, the mushroom on the touch screen where it can be turned.
class IdentifyState : public GameState
{
public:
    IdentifyState(Services &services, StateMachine &machine, IdentifySession &session);

    void Init();

    void Enter() override;
    void Exit() override;
    void Update() override;
    void Draw3D() override;

private:
    void Finish(IdentifySession::Outcome outcome);

    Services &services_;
    StateMachine &machine_;
    IdentifySession &session_;
    BookView book_;
    InspectionView view_;
    int lastPage_ = 0;
    bool finished_ = false;
};
