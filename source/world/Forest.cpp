#include "world/Forest.h"

#include "core/Random.h"
#include "render/RenderService.h"
#include "world/ShadowCaster.h"

namespace {

struct PropInfo
{
    ModelId model;
    Fixed collisionRadius; // zero = walk through
    Fixed spacing;         // minimum distance to other props when generating
    u32 weight;            // relative frequency inside the forest
    Fixed shadowRadius;
    Fixed height;
};

// Same order as PropKind.
constexpr PropInfo kPropInfo[] = {
    { ModelId::TreeRound, 0.32_fx, 2.1_fx, 30, 0.9_fx, 2.6_fx },
    { ModelId::TreeGolden, 0.32_fx, 2.1_fx, 20, 0.9_fx, 2.6_fx },
    { ModelId::TreeFir, 0.55_fx, 1.9_fx, 20, 0.75_fx, 2.4_fx },
    { ModelId::Bush, 0.45_fx, 1.2_fx, 13, 0.55_fx, 0.55_fx },
    { ModelId::Rock, 0.42_fx, 1.2_fx, 9, 0.5_fx, 0.35_fx },
    { ModelId::Stump, 0.38_fx, 1.2_fx, 3, 0.42_fx, 0.45_fx },
    { ModelId::Shrine, 0.85_fx, 3_fx, 0, 1.0_fx, 1.5_fx }, // placed once, in the middle
};

const PropInfo &Info(PropKind kind)
{
    return kPropInfo[static_cast<int>(kind)];
}

// Open areas without props.
struct Clearing
{
    Vec2 center;
    Fixed radius;
};

constexpr Vec2 kSpawn = { 0_fx, 9_fx };
constexpr Vec2 kShrine = { 0_fx, 0_fx };

constexpr Clearing kClearings[] = {
    { kSpawn, 3.2_fx },         // start
    { kShrine, 2.8_fx },        // meadow with the shrine
};

// The ground model spans +-7 and is scaled up far beyond the walkable area,
// so there is no visible edge behind the outer trees.
constexpr Fixed kGroundScale = 4_fx;
constexpr int kGenerateAttempts = 1400;
// Old stumps are where the Ölbaum-Trichterling grows, so there are always a few.
constexpr int kGuaranteedStumps = 4;
constexpr Fixed kBorderInner = 12.9_fx;

// Culling window relative to the camera focus (camera looks towards -Z).
constexpr Fixed kCullAhead = 11_fx;
constexpr Fixed kCullBehind = 3.5_fx;
constexpr Fixed kCullBaseWidth = 5.5_fx;
constexpr Fixed kCullWidening = 0.85_fx;

PropKind PickInteriorKind(Random &random)
{
    u32 total = 0;
    for (const PropInfo &info : kPropInfo)
        total += info.weight;

    u32 roll = random.Next() % total;
    for (int i = 0; i < static_cast<int>(PropKind::Count); i++)
    {
        if (roll < kPropInfo[i].weight)
            return static_cast<PropKind>(i);
        roll -= kPropInfo[i].weight;
    }
    return PropKind::TreeRound;
}

} // namespace

void Forest::Generate(u32 seed)
{
    Random random(seed);
    propCount_ = 0;

    Add(kShrine, PropKind::Shrine, 0);
    PlaceBorder(random);
    PlaceStumps(random);
    PlaceInterior(random);

    NE_Model *ground = assets_.Model(ModelId::Ground);
    NE_ModelSetCoordI(ground, 0, 0, 0);
    NE_ModelScaleI(ground, kGroundScale.Raw(), Fixed::kOne, kGroundScale.Raw());
}

void Forest::PlaceBorder(Random &random)
{
    // Staggered rows of trees around the edge form the forest wall; the outer
    // rows get sparser and fade into the fog.
    constexpr int kRows = 5;
    for (int row = 0; row < kRows; row++)
    {
        Fixed step = 1.7_fx + 0.25_fx * row;
        Fixed edge = kBorderInner + 1.2_fx * row;
        Fixed offset = (step / 2) * (row % 2);
        for (Fixed t = -edge + offset; t <= edge; t += step)
        {
            const Vec2 positions[] = { { t, -edge }, { t, edge }, { -edge, t }, { edge, t } };
            for (Vec2 p : positions)
            {
                p.x += random.Range(-0.3_fx, 0.3_fx);
                p.z += random.Range(-0.3_fx, 0.3_fx);
                PropKind kind = random.Chance(45) ? PropKind::TreeFir
                                : random.Chance(50) ? PropKind::TreeRound
                                                    : PropKind::TreeGolden;
                Add(p, kind, random.Range(0, 511));
            }
        }
    }
}

void Forest::PlaceStumps(Random &random)
{
    int placed = 0;
    for (int attempt = 0; attempt < 200 && placed < kGuaranteedStumps; attempt++)
    {
        Vec2 p = { random.Range(-10_fx, 10_fx), random.Range(-10_fx, 10_fx) };
        if (IsInClearing(p) || !IsFree(p, 3_fx))
            continue;
        if (Add(p, PropKind::Stump, random.Range(0, 511)))
            placed++;
    }
}

void Forest::PlaceInterior(Random &random)
{
    constexpr Fixed kInner = 11.4_fx;

    for (int attempt = 0; attempt < kGenerateAttempts && propCount_ < kMaxProps; attempt++)
    {
        Vec2 p = { random.Range(-kInner, kInner), random.Range(-kInner, kInner) };
        PropKind kind = PickInteriorKind(random);
        if (IsInClearing(p) || !IsFree(p, Info(kind).spacing))
            continue;

        Add(p, kind, random.Range(0, 511));
    }
}

bool Forest::IsInClearing(Vec2 position) const
{
    for (const Clearing &clearing : kClearings)
    {
        if ((position - clearing.center).LengthSq() < clearing.radius * clearing.radius)
            return true;
    }
    return false;
}

bool Forest::FindFreeSpot(Random &random, Fixed clearance, Vec2 &out) const
{
    constexpr Fixed kInner = 11_fx;
    constexpr int kAttempts = 300;
    const Clearing &start = kClearings[0];

    for (int attempt = 0; attempt < kAttempts; attempt++)
    {
        Vec2 p = { random.Range(-kInner, kInner), random.Range(-kInner, kInner) };
        if ((p - start.center).LengthSq() < start.radius * start.radius)
            continue;

        bool free = true;
        for (int i = 0; i < propCount_ && free; i++)
        {
            Fixed needed = clearance + Info(props_[i].kind).collisionRadius;
            if ((props_[i].position - p).LengthSq() < needed * needed)
                free = false;
        }
        if (free)
        {
            out = p;
            return true;
        }
    }
    return false;
}

bool Forest::IsFree(Vec2 position, Fixed spacing) const
{
    for (int i = 0; i < propCount_; i++)
    {
        const Prop &prop = props_[i];
        Fixed needed = fx::Max(spacing, Info(prop.kind).spacing);
        if ((prop.position - position).LengthSq() < needed * needed)
            return false;
    }
    return true;
}

bool Forest::Add(Vec2 position, PropKind kind, int rotation)
{
    if (propCount_ >= kMaxProps)
        return false;
    props_[propCount_++] = { position, rotation, kind };
    return true;
}

Vec2 Forest::SpawnPoint() const
{
    return kSpawn;
}

Vec2 Forest::ShrinePosition() const
{
    return kShrine;
}

Vec2 Forest::ResolveCollision(Vec2 position, Fixed radius) const
{
    constexpr Fixed kNear = 1.5_fx;

    for (int i = 0; i < propCount_; i++)
    {
        const Prop &prop = props_[i];
        Fixed propRadius = Info(prop.kind).collisionRadius;
        if (propRadius == Fixed())
            continue;

        Vec2 away = position - prop.position;
        if (fx::Abs(away.x) > kNear || fx::Abs(away.z) > kNear)
            continue;

        Fixed minDistance = radius + propRadius;
        Fixed distanceSq = away.LengthSq();
        if (distanceSq >= minDistance * minDistance)
            continue;

        Fixed distance = fx::Sqrt(distanceSq);
        if (distance == Fixed())
            position = prop.position + Vec2{ minDistance, 0_fx };
        else
            position = prop.position + away * (minDistance / distance);
    }

    position.x = fx::Clamp(position.x, -kPlayHalfSize, kPlayHalfSize);
    position.z = fx::Clamp(position.z, -kPlayHalfSize, kPlayHalfSize);
    return position;
}

bool Forest::IsNearCamera(Vec2 position, Vec2 cameraFocus)
{
    Fixed ahead = cameraFocus.z - position.z;
    if (ahead > kCullAhead || ahead < -kCullBehind)
        return false;
    Fixed halfWidth = kCullBaseWidth + fx::Max(ahead, 0_fx) * kCullWidening;
    return fx::Abs(position.x - cameraFocus.x) <= halfWidth;
}

void Forest::SelectVisible(Vec2 cameraFocus) const
{
    if (visibleValid_ && visibleFocus_.x.Raw() == cameraFocus.x.Raw() &&
        visibleFocus_.z.Raw() == cameraFocus.z.Raw())
        return;

    visibleFocus_ = cameraFocus;
    visibleValid_ = true;
    visibleCount_ = 0;

    for (int i = 0; i < propCount_; i++)
    {
        const Prop &prop = props_[i];
        if (!IsNearCamera(prop.position, cameraFocus))
            continue;

        // Keep the list sorted by distance; the farthest one drops out when full.
        Fixed distance = (prop.position - cameraFocus).LengthSq();
        if (visibleCount_ == kMaxDrawnProps && distance >= visibleDistance_[kMaxDrawnProps - 1])
            continue;

        int slot = visibleCount_ < kMaxDrawnProps ? visibleCount_++ : kMaxDrawnProps - 1;
        while (slot > 0 && visibleDistance_[slot - 1] > distance)
        {
            visibleDistance_[slot] = visibleDistance_[slot - 1];
            visible_[slot] = visible_[slot - 1];
            slot--;
        }
        visibleDistance_[slot] = distance;
        visible_[slot] = static_cast<u16>(i);
    }
}

void Forest::DrawShadows(const RenderService &render, const ShadowCaster &shadows, Vec2 cameraFocus) const
{
    if (render.ShadowAlpha() == 0)
        return;

    SelectVisible(cameraFocus);
    int count = visibleCount_ < kMaxShadowProps ? visibleCount_ : kMaxShadowProps;
    for (int n = 0; n < count; n++)
    {
        const Prop &prop = props_[visible_[n]];
        shadows.Draw(render, prop.position, Info(prop.kind).shadowRadius, Info(prop.kind).height);
    }
}

void Forest::Draw(const RenderService &render, Vec2 cameraFocus) const
{
    render.ClearObjectLight();
    render.BeginPolygons(PolyGroup::Ground);
    NE_ModelDraw(assets_.Model(ModelId::Ground));

    SelectVisible(cameraFocus);
    for (int n = 0; n < visibleCount_; n++)
    {
        int index = visible_[n];
        const Prop &prop = props_[index];
        NE_Model *model = assets_.Model(Info(prop.kind).model);
        NE_ModelSetCoordI(model, prop.position.x.Raw(), 0, prop.position.z.Raw());
        NE_ModelSetRot(model, 0, prop.rotation, 0);
        render.LightObject(prop.position);
        // Neighbouring props get different IDs so overlapping trees keep their outlines.
        render.BeginPolygons(PolyGroup::Forest, static_cast<u32>(index));
        NE_ModelDraw(model);
    }
    lastDrawnProps_ = visibleCount_;
}
