#pragma once

#include "render/AssetService.h"

enum class SpeciesId : u8
{
    Steinpilz,
    SatansRoehrling,
    Champignon,
    Knollenblaetterpilz,
    Pfifferling,
    Fliegenpilz,
    OelbaumTrichterling,
    WaldgottPilz,
    Count,
};

// Species that have a page in the mushroom book (the forest-god mushroom gets
// its riddle page later).
constexpr int kBookSpeciesCount = static_cast<int>(SpeciesId::WaldgottPilz);

enum class Edibility : u8
{
    Edible,
    Poisonous,
    DeadlyPoisonous,
    Magic, // the forest-god mushroom, the offering
};

// Where a species grows in the forest.
enum class Habitat : u8
{
    Ground,
    Wood,   // in tufts on old stumps
    Shrine, // only at the shrine (placed by the story)
};

struct SpeciesInfo
{
    const char *name;
    Edibility edibility;
    Habitat habitat;
    ModelId worldModel;
    ModelId detailModel;
    u8 worldCount; // how many grow in the forest
    const char *edibilityLabel; // shown under the name in the book
};

const SpeciesInfo &Species(SpeciesId id);

inline bool IsPoisonous(SpeciesId id)
{
    Edibility e = Species(id).edibility;
    return e == Edibility::Poisonous || e == Edibility::DeadlyPoisonous;
}
