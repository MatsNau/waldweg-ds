#pragma once

#include <array>

#include "core/Random.h"
#include "math/Angle.h"
#include "math/Vec2.h"

class AssetService;
class RenderService;

// A few autumn leaves tumbling through the 3D view now and then.
class LeafParticles
{
public:
    struct Area
    {
        Vec2 centre;     // spawn around this point ...
        Fixed halfWidth; // ... within +-halfWidth on x
        Fixed depthMin;  // ... and centre.z + [depthMin, depthMax]
        Fixed depthMax;
        Fixed height;    // spawn height
    };

    LeafParticles(const AssetService &assets, u32 seed) : assets_(assets), random_(seed) {}

    // spawnChance: leaves per 1000 frames (roughly).
    void Update(const Area &area, int spawnChance);
    void Clear();
    void Draw(const RenderService &render) const;

private:
    static constexpr int kMaxLeaves = 10;

    struct Leaf
    {
        bool alive;
        Fixed x, y, z;
        Fixed fallSpeed;
        Fixed drift;
        Angle sway;
        Angle spinX;
        Angle spinY;
        s32 spinSpeedX;
        s32 spinSpeedY;
        u8 kind;
    };

    const AssetService &assets_;
    Random random_;
    std::array<Leaf, kMaxLeaves> leaves_ = {};
};
