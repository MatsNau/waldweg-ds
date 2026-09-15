#pragma once

#include <array>

#include "content/Species.h"
#include "math/Vec2.h"

class AssetService;
class Forest;
class RenderService;

struct Mushroom
{
    Vec2 position;
    Fixed height; // ground offset, e.g. on top of a stump
    SpeciesId species;
    int rotation; // Nitro Engine units
    bool present; // false once picked
};

// All mushrooms growing in the forest: placement, drawing, reach and tapping.
class MushroomField
{
public:
    static constexpr int kMaxMushrooms = 16;
    // Nina can pick mushrooms within this distance.
    static constexpr Fixed kReach = 1.7_fx;

    explicit MushroomField(const AssetService &assets) : assets_(assets) {}

    // seed: fixed layout of the normal mushrooms; godSeed: where the forest-god
    // mushroom grows (different every game).
    void Generate(const Forest &forest, u32 seed, u32 godSeed);

    // Draws present mushrooms near the camera.
    void Draw(const RenderService &render, Vec2 cameraFocus) const;

    int Count() const { return count_; }
    const Mushroom &At(int index) const { return mushrooms_[index]; }
    int RemainingCount() const;

    // The forest-god mushroom next to the shrine only shows up in the dark.
    void SetGodMushroomVisible(bool visible) { godVisible_ = visible; }
    bool IsVisible(int index) const;

    bool IsInReach(int index, Vec2 nina) const;
    // Present mushroom closest to `position` within `radius`, or -1.
    int FindNear(Vec2 position, Fixed radius) const;
    void Pick(int index) { mushrooms_[index].present = false; }

private:
    bool Add(Vec2 position, Fixed height, SpeciesId species, int rotation);
    bool Hidden(const Mushroom &m) const;

    const AssetService &assets_;
    std::array<Mushroom, kMaxMushrooms> mushrooms_ = {};
    int count_ = 0;
    bool godVisible_ = false;
};
