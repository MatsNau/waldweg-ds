#pragma once

#include <array>

#include "math/Vec2.h"
#include "render/AssetService.h"

class RenderService;
class Random;
class ShadowCaster;

enum class PropKind : u8
{
    TreeRound,
    TreeGolden,
    TreeFir,
    Bush,
    Rock,
    Stump,
    Shrine,
    Count,
};

struct Prop
{
    Vec2 position;
    int rotation; // Nitro Engine units (0-511)
    PropKind kind;
};

// The forest area: ground, generated tree/prop layout, collision and culling.
class Forest
{
public:
    // Walkable area is [-kPlayHalfSize, kPlayHalfSize] on both axes.
    static constexpr Fixed kPlayHalfSize = 12.2_fx;

    explicit Forest(const AssetService &assets) : assets_(assets) {}

    // Builds the same layout for the same seed.
    void Generate(u32 seed);

    Vec2 SpawnPoint() const;
    Vec2 ShrinePosition() const;

    // Random walkable spot at least `clearance` away from props (outside the
    // start clearing). Returns false if none was found.
    bool FindFreeSpot(Random &random, Fixed clearance, Vec2 &out) const;

    // Pushes a circle out of props and keeps it inside the walkable area.
    Vec2 ResolveCollision(Vec2 position, Fixed radius) const;

    // Draws the ground and every prop near the camera focus.
    void Draw(const RenderService &render, Vec2 cameraFocus) const;
    // Shadows of the props near the camera (translucent, draw after opaque things).
    void DrawShadows(const RenderService &render, const ShadowCaster &shadows, Vec2 cameraFocus) const;

    int PropCount() const { return propCount_; }
    const Prop &PropAt(int index) const { return props_[index]; }
    int LastDrawnProps() const { return lastDrawnProps_; }

private:
    static constexpr int kMaxProps = 420;

    void PlaceBorder(Random &random);
    void PlaceStumps(Random &random);
    void PlaceInterior(Random &random);
    bool IsFree(Vec2 position, Fixed spacing) const;
    bool IsInClearing(Vec2 position) const;
    bool Add(Vec2 position, PropKind kind, int rotation);
    static bool IsNearCamera(Vec2 position, Vec2 cameraFocus);

    const AssetService &assets_;
    std::array<Prop, kMaxProps> props_ = {};
    int propCount_ = 0;
    mutable int lastDrawnProps_ = 0;
};
