#pragma once

enum class StateId
{
    Explore,
    Identify,
    Ending,
};

// One screen / phase of the game (TITLE, EXPLORE, IDENTIFY, ... in the plan).
class GameState
{
public:
    virtual ~GameState() = default;

    virtual void Enter() {}
    virtual void Exit() {}
    virtual void Update() = 0;
    // Called inside the 3D frame.
    virtual void Draw3D() = 0;
};

// Lets states request a change without knowing the Game class.
class StateMachine
{
public:
    virtual void ChangeState(StateId id) = 0;
    // Starts the story from the beginning (after the final picture).
    virtual void StartNewGame() = 0;

protected:
    ~StateMachine() = default;
};
