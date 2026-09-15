#pragma once

#include "content/Species.h"

// Hand-over between ExploreState (a mushroom was tapped) and IdentifyState
// (the player chose a book page or put the mushroom back).
struct IdentifySession
{
    enum class Outcome : u8
    {
        None,
        Cancelled,
        Chosen,
    };

    int mushroomIndex = -1;
    SpeciesId actual = SpeciesId::Steinpilz;
    Outcome outcome = Outcome::None;
    SpeciesId chosen = SpeciesId::Steinpilz;
};
