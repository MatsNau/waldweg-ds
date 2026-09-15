#include "game/Game.h"

Game::Game(Services &services)
    : services_(services),
      explore_(services, *this, progress_, session_),
      identify_(services, *this, session_),
      ending_(services, *this)
{
}

void Game::Init()
{
    explore_.Init();
    identify_.Init();
    ending_.Init();
    explore_.StartNewGame();
#ifdef WALDWEG_BOOT_ENDING
    // make BOOT_ENDING=1: starts right in the final picture (composition checks).
    ChangeState(StateId::Ending);
#else
    ChangeState(StateId::Explore);
#endif
}

void Game::Update()
{
    if (pending_ != nullptr)
    {
        if (current_ != nullptr)
            current_->Exit();
        current_ = pending_;
        pending_ = nullptr;
        current_->Enter();
    }

    current_->Update();
}

void Game::Draw3D()
{
    if (current_ != nullptr)
        current_->Draw3D();
}

void Game::StartNewGame()
{
    explore_.StartNewGameOnEnter();
    ChangeState(StateId::Explore);
}

void Game::ChangeState(StateId id)
{
    pending_ = &StateFor(id);
}

GameState &Game::StateFor(StateId id)
{
    switch (id)
    {
        case StateId::Identify:
            return identify_;
        case StateId::Ending:
            return ending_;
        case StateId::Explore:
            break;
    }
    return explore_;
}
