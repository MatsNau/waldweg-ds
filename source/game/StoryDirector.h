#pragma once

#include "content/Items.h"
#include "content/Species.h"
#include "core/Services.h"
#include "ui/Backpack.h"

class DialogBox;
class GameProgress;
class Mats;
class Nina;

// The story gates of the plan: basket tutorial, scarf when it gets cold,
// lantern when it gets dark. Reacts to game events, unlocks items, advances
// the time of day and talks through the dialog box.
class StoryDirector
{
public:
    StoryDirector(Services &services, GameProgress &progress, DialogBox &dialog, Nina &nina, Mats &mats)
        : services_(services), progress_(progress), dialog_(dialog), nina_(nina), mats_(mats)
    {
    }

    void Start();
    void Update();

    // Asks whether Nina may pick another mushroom; explains why not if blocked.
    bool RequestPick();
    // The player named a mushroom in the book (it is removed from the forest).
    void OnIdentified(SpeciesId actual, SpeciesId chosen);
    bool IsRestartRequested() const { return restartRequested_; }
    // True once after the bell was given: time for Shroomchen.
    bool ConsumeFinaleRequest();
    void OnItemGiven(ItemId item);

    // Nina walks near the shrine (the first visit is commented once).
    void OnNearShrine();
    void OnOfferingTaken();
    // Returns true if the tap did something (placing the offering).
    bool OnShrineTapped();

    MatsMood Mood() const;

#ifdef WALDWEG_DEBUG
    // Jumps to the dark part: basket, scarf and lantern given, blue hour.
    void DebugSkipToLantern();
#endif

private:
    static constexpr int kHappyFrames = 150;
    static constexpr int kWorriedFrames = 240;

    void OnMushroomProcessed();

    Services &services_;
    GameProgress &progress_;
    DialogBox &dialog_;
    Nina &nina_;
    Mats &mats_;
    int happyFrames_ = 0;
    int worriedFrames_ = 0;
    bool restartRequested_ = false;
    bool finaleRequested_ = false;
};
